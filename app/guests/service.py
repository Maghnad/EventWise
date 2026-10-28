"""Guest management business logic service.

Fat service layer coordinating guest CRUD, event ownership verification,
and RSVP summary calculations.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.guests.schemas import (
    CreateGuestRequest,
    GuestListResponse,
    GuestResponse,
    UpdateGuestRequest,
)
from app.shared.contracts import (
    Guest as GuestContract,
)
from app.shared.contracts import (
    GuestFaqResponse,
    GuestRsvpStatus,
    MessageResponse,
    PublicEventResponse,
    RsvpSubmissionRequest,
    RsvpSubmissionResponse,
)
from app.shared.models import Event as EventModel
from app.shared.models import Guest as GuestModel
from app.shared.models import User as UserModel
from app.shared.queries import get_event_or_404


class GuestService:
    """Service layer managing event guest lists and RSVP statuses."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _verify_event_ownership(
        db: AsyncSession,
        event_id: UUID,
        owner_id: UUID,
    ) -> EventModel:
        """Ensure the event exists and belongs to the authenticated user."""
        return await get_event_or_404(db, event_id, owner_id)

    @staticmethod
    async def _get_guest_or_404(
        db: AsyncSession,
        guest_id: UUID,
        event_id: UUID,
    ) -> GuestModel:
        """Retrieve a guest scoped to the given event.

        Args:
            db: Active async database session.
            guest_id: UUID of the guest.
            event_id: UUID of the parent event.

        Returns:
            The GuestModel if found.

        Raises:
            HTTPException: 404 if guest not found within the event.
        """
        stmt = select(GuestModel).where(
            GuestModel.id == guest_id,
            GuestModel.event_id == event_id,
        )
        result = await db.execute(stmt)
        guest = result.scalar_one_or_none()

        if guest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found.",
            )
        return guest

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    @classmethod
    async def get_guests(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
    ) -> GuestListResponse:
        """Return all guests for an event with RSVP breakdown totals.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.

        Returns:
            GuestListResponse with guests and headcount breakdown.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        guests_stmt = (
            select(GuestModel)
            .where(GuestModel.event_id == event_id)
            .order_by(GuestModel.created_at.asc())
        )
        guests_result = await db.execute(guests_stmt)
        guests = guests_result.scalars().all()

        confirmed = 0
        declined = 0
        pending = 0
        total_attending_with_plus_ones = 0

        for g in guests:
            if g.rsvp_status == GuestRsvpStatus.ATTENDING:
                confirmed += 1
                total_attending_with_plus_ones += 1 + (g.plus_ones or 0)
            elif g.rsvp_status == GuestRsvpStatus.DECLINED:
                declined += 1
            else:
                pending += 1

        return GuestListResponse(
            items=[GuestResponse.model_validate(g) for g in guests],
            total=len(guests),
            confirmed_count=confirmed,
            declined_count=declined,
            pending_count=pending,
            total_attending_with_plus_ones=total_attending_with_plus_ones,
        )

    @classmethod
    async def get_guest(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        guest_id: UUID,
    ) -> GuestResponse:
        """Retrieve a specific guest by ID.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            guest_id: UUID of the guest.

        Returns:
            GuestResponse model.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        guest = await cls._get_guest_or_404(db, guest_id, event_id)
        return GuestResponse.model_validate(guest)

    @classmethod
    async def create_guest(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: CreateGuestRequest,
    ) -> GuestResponse:
        """Add/invite a new guest to the given event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated create payload.

        Returns:
            GuestResponse of the newly created guest.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        # Check for duplicate email in event
        dup_stmt = select(GuestModel).where(
            GuestModel.event_id == event_id,
            GuestModel.email == data.email,
        )
        dup_result = await db.execute(dup_stmt)
        existing = dup_result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A guest with this email is already on the guest list.",
            )

        from app.shared.sanitizer import sanitize_text

        guest = GuestModel(
            event_id=event_id,
            full_name=sanitize_text(data.full_name or data.name) or "Guest",
            email=data.email,
            phone=sanitize_text(data.phone),
            rsvp_status=data.rsvp_status,
            dietary_restrictions=[
                sanitize_text(d) or "" for d in (data.dietary_restrictions or [])
            ],
            plus_ones=data.plus_ones,
            table_number=data.table_number,
            notes=sanitize_text(data.notes),
        )
        db.add(guest)
        await db.flush()
        await db.refresh(guest)
        return GuestResponse.model_validate(guest)

    @classmethod
    async def update_guest(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        guest_id: UUID,
        data: UpdateGuestRequest,
    ) -> GuestResponse:
        """Update a specific guest by ID.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            guest_id: UUID of the guest to update.
            data: Validated update payload.

        Returns:
            GuestResponse of the updated guest.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        guest = await cls._get_guest_or_404(db, guest_id, event_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        update_data.pop("guest_id", None)
        update_data.pop("name", None)
        update_data.pop("dietary", None)
        update_data.pop("plus_one", None)

        if data.name is not None and "full_name" not in update_data:
            guest.full_name = data.name
        if data.dietary is not None and "dietary_restrictions" not in update_data:
            diet = data.dietary
            guest.dietary_restrictions = [diet] if isinstance(diet, str) else diet
        if data.plus_one is not None and "plus_ones" not in update_data:
            val = data.plus_one
            guest.plus_ones = 1 if val is True else (0 if val is False else int(val))

        for field, value in update_data.items():
            setattr(guest, field, value)

        await db.flush()
        await db.refresh(guest)
        return GuestResponse.model_validate(guest)

    @classmethod
    async def update_or_upsert_guest(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        data: UpdateGuestRequest,
    ) -> GuestResponse:
        """Update a guest, identifying by guest_id, email, or updating/creating.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            data: Validated update payload.

        Returns:
            GuestResponse of the updated or newly created guest.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        target_id = data.guest_id or data.id
        if target_id is not None:
            return await cls.update_guest(db, user, event_id, target_id, data)

        if data.email:
            stmt = select(GuestModel).where(
                GuestModel.event_id == event_id,
                GuestModel.email == data.email,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is not None:
                return await cls.update_guest(db, user, event_id, existing.id, data)

        # Target first existing guest if any
        existing_any = await db.execute(
            select(GuestModel)
            .where(GuestModel.event_id == event_id)
            .order_by(GuestModel.created_at.asc())
        )
        first_guest = existing_any.scalars().first()
        if first_guest is not None:
            return await cls.update_guest(db, user, event_id, first_guest.id, data)

        # Else create new
        if not data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required to create a new guest.",
            )
        create_payload = CreateGuestRequest(
            name=data.name or data.full_name or "Guest",
            full_name=data.full_name or data.name or "Guest",
            email=data.email,
            phone=data.phone,
            rsvp_status=data.rsvp_status or GuestRsvpStatus.PENDING,
            dietary=data.dietary,
            dietary_restrictions=data.dietary_restrictions or [],
            plus_one=data.plus_one or data.plus_ones or 0,
            plus_ones=data.plus_ones or 0,
            table_number=data.table_number,
            notes=data.notes or "",
        )
        return await cls.create_guest(db, user, event_id, create_payload)

    @classmethod
    async def delete_guest(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        guest_id: UUID,
    ) -> MessageResponse:
        """Delete a guest from the event.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            guest_id: UUID of the guest to delete.

        Returns:
            MessageResponse confirming deletion.
        """
        await cls._verify_event_ownership(db, event_id, user.id)
        guest = await cls._get_guest_or_404(db, guest_id, event_id)

        await db.delete(guest)
        await db.flush()

        return MessageResponse(
            success=True,
            message="Guest deleted successfully.",
        )

    @classmethod
    async def delete_guest_by_identifier(
        cls,
        db: AsyncSession,
        user: UserModel,
        event_id: UUID,
        guest_id: UUID | None = None,
        email: str | None = None,
    ) -> MessageResponse:
        """Delete a guest by either guest_id or email.

        Args:
            db: Active async database session.
            user: Authenticated user model.
            event_id: UUID of the parent event.
            guest_id: Optional UUID of the guest.
            email: Optional email of the guest.

        Returns:
            MessageResponse confirming deletion.
        """
        await cls._verify_event_ownership(db, event_id, user.id)

        if guest_id is not None:
            return await cls.delete_guest(db, user, event_id, guest_id)

        if email:
            stmt = select(GuestModel).where(
                GuestModel.event_id == event_id,
                GuestModel.email == email,
            )
            result = await db.execute(stmt)
            guest = result.scalar_one_or_none()
            if guest is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Guest not found.",
                )
            await db.delete(guest)
            await db.flush()
            return MessageResponse(
                success=True,
                message="Guest deleted successfully.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either guest_id or email must be provided to delete guest.",
        )

    # ------------------------------------------------------------------
    # Public (No Auth) RSVP & Guest FAQ methods
    # ------------------------------------------------------------------

    @classmethod
    async def get_public_event(
        cls,
        db: AsyncSession,
        event_id: UUID,
    ) -> PublicEventResponse:
        """Fetch basic public event metadata for unauthenticated guest RSVP."""
        stmt = select(EventModel).where(EventModel.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found.",
            )
        return PublicEventResponse(
            id=event.id,
            title=event.title,
            description=event.description or "",
            event_type=event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type),
            start_date=event.start_date,
            end_date=event.end_date,
            location=event.location or "",
        )

    @classmethod
    async def submit_public_rsvp(
        cls,
        db: AsyncSession,
        event_id: UUID,
        data: RsvpSubmissionRequest,
    ) -> RsvpSubmissionResponse:
        """Record or update a public RSVP submission from a guest."""
        stmt = select(EventModel).where(EventModel.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found.",
            )

        guest_stmt = select(GuestModel).where(
            GuestModel.event_id == event_id,
            GuestModel.email == data.email,
        )
        res = await db.execute(guest_stmt)
        guest = res.scalar_one_or_none()

        from app.shared.sanitizer import sanitize_text

        raw_name = data.full_name or data.email.split("@")[0].replace(".", " ").title()
        guest_name = sanitize_text(raw_name) or "Guest"
        safe_dietary = [
            sanitize_text(d) or "" for d in (data.dietary_restrictions or [])
        ]
        safe_notes = sanitize_text(data.notes)

        if guest is None:
            guest = GuestModel(
                event_id=event_id,
                full_name=guest_name,
                email=data.email,
                rsvp_status=data.rsvp_status,
                dietary_restrictions=safe_dietary,
                plus_ones=data.plus_ones,
                notes=safe_notes,
            )
            db.add(guest)
        else:
            guest.rsvp_status = data.rsvp_status
            guest.plus_ones = data.plus_ones
            guest.dietary_restrictions = safe_dietary
            if safe_notes:
                guest.notes = (
                    f"{guest.notes}\n{safe_notes}".strip()
                    if guest.notes
                    else safe_notes
                )
            if guest_name:
                guest.full_name = guest_name

        await db.flush()
        await db.refresh(guest)
        await db.commit()

        status_text = (
            "attending"
            if guest.rsvp_status == GuestRsvpStatus.ATTENDING
            else "declined"
        )
        return RsvpSubmissionResponse(
            success=True,
            message=f"Thank you! Your RSVP has been confirmed as {status_text}.",
            guest=GuestContract.model_validate(guest),
        )

    @classmethod
    async def answer_guest_faq(
        cls,
        db: AsyncSession,
        event_id: UUID,
        question: str,
    ) -> GuestFaqResponse:
        """Answer guest inquiries using event details and situational context."""
        stmt = select(EventModel).where(EventModel.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
            )

        q = question.lower()
        title = event.title
        loc = event.location or "the main event venue"
        start_str = (
            event.start_date.strftime("%A, %B %d, %Y at %I:%M %p")
            if event.start_date
            else "the scheduled date"
        )

        if any(w in q for w in ["dress", "attire", "wear", "code", "outfit"]):
            answer = f"The recommended attire for {title} is cocktail / semi-formal, suited for a {event.event_type.value if hasattr(event.event_type, 'value') else event.event_type} gathering."
        elif any(
            w in q
            for w in [
                "where",
                "location",
                "address",
                "venue",
                "place",
                "park",
                "parking",
            ]
        ):
            answer = f"{title} takes place at {loc}. Designated guest parking and drop-off zones are available near the entrance."
        elif any(w in q for w in ["when", "time", "date", "start", "schedule", "hour"]):
            answer = f"{title} is scheduled for {start_str}. We recommend arriving 15 minutes prior to start time."
        elif any(
            w in q
            for w in [
                "diet",
                "food",
                "vegan",
                "vegetarian",
                "allergy",
                "gluten",
                "halal",
                "kosher",
                "menu",
            ]
        ):
            answer = "All special dietary requirements and food allergies are accommodated by catering! Please list your dietary restrictions when submitting your RSVP."
        elif any(
            w in q
            for w in ["kid", "child", "children", "baby", "plus one", "guest", "invite"]
        ):
            answer = "Please refer to your RSVP form for your allocated plus-one headcount. Feel free to leave a note on your RSVP for any additional family inquiries."
        else:
            answer = f"Thanks for inquiring about {title}! The event is taking place at {loc} on {start_str}. If you have special questions, leave a note with your RSVP or reach out to the event host."

        return GuestFaqResponse(
            answer=answer,
            event_title=title,
            suggested_questions=[
                "What is the dress code?",
                "Where is the venue and parking?",
                "What time does the event begin?",
                "How are dietary restrictions handled?",
            ],
        )
