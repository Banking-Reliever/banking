"""Domain-layer error codes — mirror commands.yaml.errors and schema enums."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainError(Exception):
    code: str
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.message}"


class IdentityFieldsMissing(DomainError):
    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            code="IDENTITY_FIELDS_MISSING",
            message=f"Missing required identity fields: {', '.join(missing)}",
        )


class CallerSuppliedInternalId(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="CALLER_SUPPLIED_INTERNAL_ID",
            message="internal_id is server-minted; the request must not carry one.",
        )


class AnchorNotFound(DomainError):
    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_NOT_FOUND",
            message=f"No anchor found for internal_id={internal_id}.",
        )


class AnchorArchived(DomainError):
    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_ARCHIVED",
            message=(
                f"Anchor {internal_id} is ARCHIVED; UPDATE is not accepted "
                "in this state. Issue RESTORE first."
            ),
        )


class AnchorAlreadyArchived(DomainError):
    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_ALREADY_ARCHIVED",
            message=f"Anchor {internal_id} is already ARCHIVED.",
        )


class AnchorNotArchived(DomainError):
    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_NOT_ARCHIVED",
            message=f"Anchor {internal_id} is not ARCHIVED — nothing to restore.",
        )


class AnchorPseudonymised(DomainError):
    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_PSEUDONYMISED",
            message=(
                f"Anchor {internal_id} is PSEUDONYMISED — terminal state, "
                "no further mutation is accepted."
            ),
        )


class NoFieldsToUpdate(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="NO_FIELDS_TO_UPDATE",
            message="The UPDATE payload carries no mutable field.",
        )


class InternalIdImmutable(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="INTERNAL_ID_IMMUTABLE",
            message="internal_id is immutable for the lifetime of the anchor (INV.BEN.002).",
        )


class InvalidReason(DomainError):
    def __init__(self, scope: str, reason: str | None) -> None:
        super().__init__(
            code="INVALID_REASON",
            message=f"{scope}: reason {reason!r} is missing or outside the canonical enum.",
        )
