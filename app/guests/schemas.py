"""Guest Management Pydantic schemas.

Supports canonical contracts as well as shorthand fields
(name, email, rsvp_status, dietary, plus_one) for guest CRUD.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import EmailStr, Field, model_validator

from app.shared.contracts import (
    ContractModel,
    GuestRsvpStatus,
    MessageResponse,
)
from app.shared.contracts import (
    Guest as GuestContract,
)


class GuestResponse(GuestContract):
    """Guest response entity with convenience name, dietary, plus_one fields."""

    name: str = ""
    dietary: list[str] = Field(default_factory=list)
    plus_one: int = 0

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            name_val = data.get("name") or data.get("full_name", "")
            data["name"] = name_val
            if not data.get("full_name"):
                data["full_name"] = name_val

            diet = data.get("dietary") or data.get("dietary_restrictions", [])
            if isinstance(diet, str):
                diet = [diet]
            data["dietary"] = diet
            if not data.get("dietary_restrictions"):
                data["dietary_restrictions"] = diet

            p_one = data.get("plus_one")
            if p_one is None:
                p_one = data.get("plus_ones", 0)
            if isinstance(p_one, bool):
                p_one = 1 if p_one else 0
            data["plus_one"] = p_one
            if "plus_ones" not in data or data["plus_ones"] is None:
                data["plus_ones"] = p_one
            return data

        if hasattr(data, "full_name"):
            # ORM model
            p_ones = data.plus_ones or 0
            dietary_list = data.dietary_restrictions or []
            return {
                "id": data.id,
                "event_id": data.event_id,
                "full_name": data.full_name,
                "name": data.full_name,
                "email": data.email,
                "phone": data.phone,
                "rsvp_status": data.rsvp_status,
                "dietary_restrictions": dietary_list,
                "dietary": dietary_list,
                "plus_ones": p_ones,
                "plus_one": p_ones,
                "table_number": data.table_number,
                "notes": data.notes,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class GuestListResponse(ContractModel):
    """Paginated guest list with RSVP summary breakdown."""

    items: list[GuestResponse]
    total: int
    confirmed_count: int
    declined_count: int
    pending_count: int
    total_attending_with_plus_ones: int


class CreateGuestRequest(ContractModel):
    """Payload for creating/inviting a guest.

    Supports name, email, rsvp_status, dietary, plus_one.
    """

    name: str = ""
    full_name: str = ""
    email: EmailStr
    phone: str | None = None
    rsvp_status: GuestRsvpStatus = GuestRsvpStatus.PENDING
    dietary: str | list[str] | None = None
    dietary_restrictions: list[str] = Field(default_factory=list)
    plus_one: int | bool | None = None
    plus_ones: int = 0
    table_number: int | None = None
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # name <-> full_name
            if data.get("name") and not data.get("full_name"):
                data["full_name"] = data["name"]
            elif data.get("full_name") and not data.get("name"):
                data["name"] = data["full_name"]
            elif not data.get("full_name") and not data.get("name"):
                data["full_name"] = "Guest"
                data["name"] = "Guest"

            # dietary <-> dietary_restrictions
            if data.get("dietary") is not None:
                diet = data["dietary"]
                if isinstance(diet, str):
                    data["dietary_restrictions"] = [diet]
                elif isinstance(diet, list):
                    data["dietary_restrictions"] = diet
            elif data.get("dietary_restrictions"):
                data["dietary"] = data["dietary_restrictions"]

            # plus_one <-> plus_ones
            if data.get("plus_one") is not None:
                val = data["plus_one"]
                if isinstance(val, bool):
                    data["plus_ones"] = 1 if val else 0
                else:
                    data["plus_ones"] = int(val)
            elif "plus_ones" in data and data["plus_ones"] is not None:
                data["plus_one"] = int(data["plus_ones"])

            # Map confirmed -> attending
            status_val = data.get("rsvp_status")
            if isinstance(status_val, str) and status_val.lower() == "confirmed":
                data["rsvp_status"] = GuestRsvpStatus.ATTENDING
        return data


class UpdateGuestRequest(ContractModel):
    """Payload for updating guest details."""

    id: UUID | None = None
    guest_id: UUID | None = None
    name: str | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    rsvp_status: GuestRsvpStatus | None = None
    dietary: str | list[str] | None = None
    dietary_restrictions: list[str] | None = None
    plus_one: int | bool | None = None
    plus_ones: int | None = None
    table_number: int | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("name") and not data.get("full_name"):
                data["full_name"] = data["name"]
            if data.get("dietary") is not None:
                diet = data["dietary"]
                if isinstance(diet, str):
                    data["dietary_restrictions"] = [diet]
                elif isinstance(diet, list):
                    data["dietary_restrictions"] = diet
            if data.get("plus_one") is not None:
                val = data["plus_one"]
                if isinstance(val, bool):
                    data["plus_ones"] = 1 if val else 0
                else:
                    data["plus_ones"] = int(val)
            if "id" in data and "guest_id" not in data:
                data["guest_id"] = data["id"]
            status_val = data.get("rsvp_status")
            if isinstance(status_val, str) and status_val.lower() == "confirmed":
                data["rsvp_status"] = GuestRsvpStatus.ATTENDING
        return data


__all__ = [
    "CreateGuestRequest",
    "GuestListResponse",
    "GuestResponse",
    "GuestRsvpStatus",
    "MessageResponse",
    "UpdateGuestRequest",
]
