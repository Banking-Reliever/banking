"""DTOs crossing the application boundary.

These are *internal* — the presentation layer maps them to JSON; the schema
validator works on dicts. The wire-format BeneficiaryAnchor is what the
HTTP responses serialise.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, ClassVar, Final

from ..domain.value_objects import Actor, ContactDetails, PostalAddress


class _Unset:
    _instance: ClassVar["_Unset | None"] = None

    def __new__(cls) -> "_Unset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover
        return "<UNSET>"

    def __bool__(self) -> bool:  # pragma: no cover
        return False


UNSET: Final[_Unset] = _Unset()


@dataclass(frozen=True, slots=True)
class ContactDetailsUpdate:
    email: str | None | _Unset = UNSET
    phone: str | None | _Unset = UNSET
    postal_address: PostalAddress | None | _Unset = UNSET

    @property
    def has_any_mutation(self) -> bool:
        return not (
            self.email is UNSET
            and self.phone is UNSET
            and self.postal_address is UNSET
        )

    def merge(self, current: ContactDetails | None) -> ContactDetails | None:
        base = current or ContactDetails(email=None, phone=None, postal_address=None)
        new_email = base.email if self.email is UNSET else self.email
        new_phone = base.phone if self.phone is UNSET else self.phone
        new_postal = base.postal_address if self.postal_address is UNSET else self.postal_address

        if new_email is None and new_phone is None and new_postal is None:
            return None
        return ContactDetails(
            email=new_email,
            phone=new_phone,
            postal_address=new_postal,
        )


@dataclass(frozen=True, slots=True)
class UpdateFields:
    last_name: str | _Unset = UNSET
    first_name: str | _Unset = UNSET
    date_of_birth: date | _Unset = UNSET
    contact_details: ContactDetailsUpdate | _Unset = UNSET
    attempts_internal_id_mutation: bool = False

    @property
    def has_any_mutation(self) -> bool:
        if not (
            self.last_name is UNSET
            and self.first_name is UNSET
            and self.date_of_birth is UNSET
        ):
            return True
        if isinstance(self.contact_details, ContactDetailsUpdate):
            return self.contact_details.has_any_mutation
        return False

    def merge_last_name(self, current: str | None) -> str | None:
        return current if self.last_name is UNSET else self.last_name

    def merge_first_name(self, current: str | None) -> str | None:
        return current if self.first_name is UNSET else self.first_name

    def merge_date_of_birth(self, current: date | None) -> date | None:
        return current if self.date_of_birth is UNSET else self.date_of_birth

    def merge_contact_details(self, current: ContactDetails | None) -> ContactDetails | None:
        if self.contact_details is UNSET:
            return current
        assert isinstance(self.contact_details, ContactDetailsUpdate)
        return self.contact_details.merge(current)


@dataclass(frozen=True, slots=True)
class MintAnchorCommandDto:
    client_request_id: str
    last_name: str
    first_name: str
    date_of_birth: date
    contact_details: ContactDetails | None
    actor: Actor


@dataclass(frozen=True, slots=True)
class UpdateAnchorCommandDto:
    internal_id: str
    command_id: str
    fields: UpdateFields
    actor: Actor


@dataclass(frozen=True, slots=True)
class ArchiveAnchorCommandDto:
    internal_id: str
    command_id: str
    reason: str
    actor: Actor
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class RestoreAnchorCommandDto:
    internal_id: str
    command_id: str
    reason: str
    actor: Actor
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class BeneficiaryAnchorDto:
    internal_id: str
    last_name: str | None
    first_name: str | None
    date_of_birth: date | None
    contact_details: dict[str, Any] | None
    anchor_status: str
    creation_date: date
    pseudonymized_at: datetime | None
    revision: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "internal_id": self.internal_id,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "contact_details": self.contact_details,
            "anchor_status": self.anchor_status,
            "creation_date": self.creation_date.isoformat(),
            "pseudonymized_at": self.pseudonymized_at.isoformat() if self.pseudonymized_at else None,
            "revision": self.revision,
        }


__all__ = [
    "ArchiveAnchorCommandDto",
    "BeneficiaryAnchorDto",
    "ContactDetailsUpdate",
    "MintAnchorCommandDto",
    "RestoreAnchorCommandDto",
    "UNSET",
    "UpdateAnchorCommandDto",
    "UpdateFields",
    "_Unset",
]
