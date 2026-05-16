"""Domain events emitted by the aggregate (in-process; not the wire RVT yet)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Union

from .value_objects import Actor, ContactDetails, InternalId, TransitionKind


@dataclass(frozen=True, slots=True)
class AnchorMinted:
    internal_id: InternalId
    last_name: str
    first_name: str
    date_of_birth: date
    contact_details: ContactDetails | None
    creation_date: date
    revision: int
    transition_kind: TransitionKind
    command_id: str
    occurred_at: datetime
    actor: Actor


@dataclass(frozen=True, slots=True)
class AnchorUpdated:
    internal_id: InternalId
    last_name: str
    first_name: str
    date_of_birth: date
    contact_details: ContactDetails | None
    creation_date: date
    revision: int
    transition_kind: TransitionKind
    command_id: str
    occurred_at: datetime
    actor: Actor


@dataclass(frozen=True, slots=True)
class AnchorArchived:
    internal_id: InternalId
    last_name: str | None
    first_name: str | None
    date_of_birth: date | None
    contact_details: ContactDetails | None
    creation_date: date
    revision: int
    transition_kind: TransitionKind
    command_id: str
    occurred_at: datetime
    actor: Actor
    reason: str
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class AnchorRestored:
    internal_id: InternalId
    last_name: str | None
    first_name: str | None
    date_of_birth: date | None
    contact_details: ContactDetails | None
    creation_date: date
    revision: int
    transition_kind: TransitionKind
    command_id: str
    occurred_at: datetime
    actor: Actor
    reason: str
    comment: str | None = None


TransitionEvent = Union[AnchorMinted, AnchorUpdated, AnchorArchived, AnchorRestored]


__all__ = [
    "AnchorMinted",
    "AnchorUpdated",
    "AnchorArchived",
    "AnchorRestored",
    "TransitionEvent",
]
