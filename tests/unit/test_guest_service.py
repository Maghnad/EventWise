"""Unit tests for GuestService business logic.

Tests guest CRUD, event ownership isolation, RSVP headcount calculations, and email uniqueness.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.service import EventService
from app.guests.schemas import CreateGuestRequest, UpdateGuestRequest
from app.guests.service import GuestService
from app.shared.contracts import (
    CreateEventRequest,
    EventStatus,
    EventType,
    GuestRsvpStatus,
    RsvpSubmissionRequest,
    SignupRequest,
)
from app.users.service import UserService

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
async def user_and_event(
    db_session: AsyncSession,
) -> tuple[object, object]:
    """Create a test user and an associated event."""
    user = await UserService.signup(
        db_session,
        SignupRequest(
            email=f"guest_user_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Guest Manager",
        ),
    )
    user_model = await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, user.user.id
    )

    now = datetime.now(UTC)
    event_data = CreateEventRequest(
        title="Guest Management Gala",
        description="Testing guest lists",
        event_type=EventType.SOCIAL,
        location="Metropolitan Club",
        start_date=now + timedelta(days=30),
        end_date=now + timedelta(days=30, hours=5),
        estimated_guest_count=80,
        total_budget=Decimal("25000.00"),
        currency="USD",
        status=EventStatus.PLANNING,
    )
    event = await EventService.create_event(db_session, user_model, event_data)
    return user_model, event


@pytest.fixture
async def other_user(db_session: AsyncSession) -> object:
    """Create an unrelated user for isolation testing."""
    resp = await UserService.signup(
        db_session,
        SignupRequest(
            email=f"guest_intruder_{uuid4().hex[:6]}@example.com",
            password="SecurePassword123!",
            full_name="Guest Intruder",
        ),
    )
    return await db_session.get(
        __import__("app.shared.models", fromlist=["User"]).User, resp.user.id
    )


# ==============================================================================
# Unit Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_guest_with_all_shorthand_fields(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.create_guest maps name, email, rsvp_status, dietary, plus_one."""
    user, event = user_and_event
    req = CreateGuestRequest(
        name="Alice Walker",
        email="alice.walker@example.com",
        rsvp_status=GuestRsvpStatus.ATTENDING,
        dietary=["Gluten-Free", "Vegetarian"],
        plus_one=1,
    )
    guest = await GuestService.create_guest(db_session, user, event.id, req)

    assert guest.name == "Alice Walker"
    assert guest.full_name == "Alice Walker"
    assert guest.email == "alice.walker@example.com"
    assert guest.rsvp_status == GuestRsvpStatus.ATTENDING
    assert guest.dietary == ["Gluten-Free", "Vegetarian"]
    assert guest.plus_one == 1
    assert guest.plus_ones == 1
    assert guest.event_id == event.id


@pytest.mark.asyncio
async def test_create_guest_duplicate_email_400(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.create_guest rejects duplicate email within same event."""
    user, event = user_and_event
    req = CreateGuestRequest(
        name="Bob Smith",
        email="bob@example.com",
    )
    await GuestService.create_guest(db_session, user, event.id, req)

    with pytest.raises(HTTPException) as exc_info:
        await GuestService.create_guest(db_session, user, event.id, req)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_guests_headcount_breakdown(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.get_guests accurately totals RSVP breakdown and plus-ones."""
    user, event = user_and_event

    # 1 Attending with 2 plus ones = 3 total headcount
    await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(
            name="Charlie",
            email="charlie@example.com",
            rsvp_status=GuestRsvpStatus.ATTENDING,
            plus_one=2,
        ),
    )
    # 1 Declined
    await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(
            name="David",
            email="david@example.com",
            rsvp_status=GuestRsvpStatus.DECLINED,
        ),
    )
    # 1 Pending
    await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(
            name="Eve",
            email="eve@example.com",
            rsvp_status=GuestRsvpStatus.PENDING,
        ),
    )

    overview = await GuestService.get_guests(db_session, user, event.id)

    assert overview.total == 3
    assert overview.confirmed_count == 1
    assert overview.declined_count == 1
    assert overview.pending_count == 1
    assert overview.total_attending_with_plus_ones == 3


@pytest.mark.asyncio
async def test_update_guest_details(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.update_guest updates specific fields."""
    user, event = user_and_event
    guest = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(
            name="Frank",
            email="frank@example.com",
            rsvp_status=GuestRsvpStatus.PENDING,
        ),
    )

    updated = await GuestService.update_guest(
        db_session,
        user,
        event.id,
        guest.id,
        UpdateGuestRequest(
            rsvp_status=GuestRsvpStatus.ATTENDING,
            plus_one=1,
            dietary=["Vegan"],
        ),
    )

    assert updated.id == guest.id
    assert updated.rsvp_status == GuestRsvpStatus.ATTENDING
    assert updated.plus_one == 1
    assert updated.dietary == ["Vegan"]


@pytest.mark.asyncio
async def test_delete_guest(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.delete_guest removes guest from event."""
    user, event = user_and_event
    guest = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(
            name="Grace",
            email="grace@example.com",
        ),
    )

    resp = await GuestService.delete_guest(db_session, user, event.id, guest.id)
    assert resp.success is True

    guests = await GuestService.get_guests(db_session, user, event.id)
    assert guests.total == 0


@pytest.mark.asyncio
async def test_guest_ownership_isolation(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
    other_user: object,
) -> None:
    """Another user accessing the event's guests receives 404."""
    _user, event = user_and_event

    with pytest.raises(HTTPException) as exc_info:
        await GuestService.get_guests(db_session, other_user, event.id)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        await GuestService.create_guest(
            db_session,
            other_user,
            event.id,
            CreateGuestRequest(
                name="Spy",
                email="spy@example.com",
            ),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_guest_success_and_404(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.get_guest retrieves a single guest or raises 404."""
    user, event = user_and_event
    created = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(name="Hannah", email="hannah@example.com"),
    )

    found = await GuestService.get_guest(db_session, user, event.id, created.id)
    assert found.id == created.id
    assert found.email == "hannah@example.com"

    fake_id = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await GuestService.get_guest(db_session, user, event.id, fake_id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_guest_shorthand_fields(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.update_guest handles name, dietary string, plus_one bool/int."""
    user, event = user_and_event
    guest = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(name="Ian", email="ian@example.com"),
    )

    # Update with shorthand name and dietary as single string, plus_one as boolean True
    updated = await GuestService.update_guest(
        db_session,
        user,
        event.id,
        guest.id,
        UpdateGuestRequest(name="Ian S.", dietary="Nut-Free", plus_one=True),
    )
    assert updated.full_name == "Ian S."
    assert updated.dietary_restrictions == ["Nut-Free"]
    assert updated.plus_ones == 1

    # Update with plus_one as boolean False
    updated2 = await GuestService.update_guest(
        db_session,
        user,
        event.id,
        guest.id,
        UpdateGuestRequest(plus_one=False),
    )
    assert updated2.plus_ones == 0


@pytest.mark.asyncio
async def test_update_or_upsert_guest_scenarios(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.update_or_upsert_guest tests target_id, email match, first guest, and create."""
    user, event = user_and_event

    # 1. Update by target_id
    guest1 = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(name="Jack", email="jack@example.com"),
    )
    res1 = await GuestService.update_or_upsert_guest(
        db_session,
        user,
        event.id,
        UpdateGuestRequest(guest_id=guest1.id, name="Jack Updated"),
    )
    assert res1.full_name == "Jack Updated"

    # 2. Update by matching email
    res2 = await GuestService.update_or_upsert_guest(
        db_session,
        user,
        event.id,
        UpdateGuestRequest(email="jack@example.com", notes="VIP guest"),
    )
    assert res2.id == guest1.id
    assert res2.notes == "VIP guest"

    # 3. Fall-through to first guest when no email or id specified
    res3 = await GuestService.update_or_upsert_guest(
        db_session,
        user,
        event.id,
        UpdateGuestRequest(notes="Primary table"),
    )
    assert res3.id == guest1.id
    assert res3.notes == "Primary table"


@pytest.mark.asyncio
async def test_update_or_upsert_guest_create_and_validation(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.update_or_upsert_guest creates a new guest when none exist, or raises 400 if no email."""
    user, event = user_and_event

    # Event has no guests yet
    # Missing email raises 400
    with pytest.raises(HTTPException) as exc_info:
        await GuestService.update_or_upsert_guest(
            db_session,
            user,
            event.id,
            UpdateGuestRequest(name="Nameless"),
        )
    assert exc_info.value.status_code == 400

    # With email creates guest
    created = await GuestService.update_or_upsert_guest(
        db_session,
        user,
        event.id,
        UpdateGuestRequest(name="Kelly", email="kelly@example.com", rsvp_status=GuestRsvpStatus.ATTENDING),
    )
    assert created.full_name == "Kelly"
    assert created.email == "kelly@example.com"
    assert created.rsvp_status == GuestRsvpStatus.ATTENDING


@pytest.mark.asyncio
async def test_delete_guest_by_identifier_scenarios(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.delete_guest_by_identifier handles guest_id, email, 404, and 400."""
    user, event = user_and_event
    g1 = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(name="Leo", email="leo@example.com"),
    )
    g2 = await GuestService.create_guest(
        db_session,
        user,
        event.id,
        CreateGuestRequest(name="Mia", email="mia@example.com"),
    )

    # 1. Delete by guest_id
    del1 = await GuestService.delete_guest_by_identifier(db_session, user, event.id, guest_id=g1.id)
    assert del1.success is True

    # 2. Delete by email
    del2 = await GuestService.delete_guest_by_identifier(db_session, user, event.id, email="mia@example.com")
    assert del2.success is True

    # 3. Email not found -> 404
    with pytest.raises(HTTPException) as exc_info:
        await GuestService.delete_guest_by_identifier(db_session, user, event.id, email="nobody@example.com")
    assert exc_info.value.status_code == 404

    # 4. Neither provided -> 400
    with pytest.raises(HTTPException) as exc_info2:
        await GuestService.delete_guest_by_identifier(db_session, user, event.id)
    assert exc_info2.value.status_code == 400


@pytest.mark.asyncio
async def test_public_event_and_rsvp_submission(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService public methods: get_public_event and submit_public_rsvp."""
    _user, event = user_and_event

    # 1. get_public_event success
    pub_event = await GuestService.get_public_event(db_session, event.id)
    assert pub_event.id == event.id
    assert pub_event.title == event.title
    assert pub_event.location == event.location

    # 2. get_public_event not found -> 404
    with pytest.raises(HTTPException) as exc_info:
        await GuestService.get_public_event(db_session, uuid4())
    assert exc_info.value.status_code == 404

    # 3. submit_public_rsvp for new guest
    req = RsvpSubmissionRequest(
        email="guest.external@example.com",
        full_name="External Guest",
        rsvp_status=GuestRsvpStatus.ATTENDING,
        plus_ones=2,
        dietary_restrictions=["Vegetarian"],
        notes="Allergic to peanuts",
    )
    rsvp_resp = await GuestService.submit_public_rsvp(db_session, event.id, req)
    assert rsvp_resp.success is True
    assert "confirmed as attending" in rsvp_resp.message
    assert rsvp_resp.guest.email == "guest.external@example.com"
    assert rsvp_resp.guest.plus_ones == 2

    # 4. submit_public_rsvp update existing guest to declined
    req_update = RsvpSubmissionRequest(
        email="guest.external@example.com",
        rsvp_status=GuestRsvpStatus.DECLINED,
        plus_ones=0,
        dietary_restrictions=[],
        notes="Cannot make it unfortunately",
    )
    rsvp_update = await GuestService.submit_public_rsvp(db_session, event.id, req_update)
    assert rsvp_update.success is True
    assert "confirmed as declined" in rsvp_update.message
    assert rsvp_update.guest.rsvp_status == GuestRsvpStatus.DECLINED
    assert "Cannot make it unfortunately" in rsvp_update.guest.notes

    # 5. submit_public_rsvp for non-existent event -> 404
    with pytest.raises(HTTPException) as exc_info2:
        await GuestService.submit_public_rsvp(db_session, uuid4(), req)
    assert exc_info2.value.status_code == 404


@pytest.mark.asyncio
async def test_answer_guest_faq_topics(
    db_session: AsyncSession,
    user_and_event: tuple[object, object],
) -> None:
    """GuestService.answer_guest_faq returns targeted contextual responses."""
    _user, event = user_and_event

    # 1. Dress code
    faq1 = await GuestService.answer_guest_faq(db_session, event.id, "What is the dress code or attire?")
    assert "cocktail" in faq1.answer.lower() or "attire" in faq1.answer.lower()

    # 2. Location / parking
    faq2 = await GuestService.answer_guest_faq(db_session, event.id, "Where is the venue and is parking available?")
    assert "metropolitan club" in faq2.answer.lower()
    assert "parking" in faq2.answer.lower()

    # 3. Schedule / timing
    faq3 = await GuestService.answer_guest_faq(db_session, event.id, "What time does the event start and schedule?")
    assert "scheduled" in faq3.answer.lower() or "time" in faq3.answer.lower()

    # 4. Dietary
    faq4 = await GuestService.answer_guest_faq(db_session, event.id, "Do you have vegan or vegetarian food for allergies?")
    assert "dietary" in faq4.answer.lower() or "catering" in faq4.answer.lower()

    # 5. Kids / plus-one
    faq5 = await GuestService.answer_guest_faq(db_session, event.id, "Can I bring my child and plus one guest?")
    assert "plus-one" in faq5.answer.lower() or "headcount" in faq5.answer.lower()

    # 6. General question
    faq6 = await GuestService.answer_guest_faq(db_session, event.id, "Can you tell me about the weather?")
    assert "thanks for inquiring" in faq6.answer.lower()

    # 7. Non-existent event -> 404
    with pytest.raises(HTTPException) as exc_info:
        await GuestService.answer_guest_faq(db_session, uuid4(), "Hello?")
    assert exc_info.value.status_code == 404

