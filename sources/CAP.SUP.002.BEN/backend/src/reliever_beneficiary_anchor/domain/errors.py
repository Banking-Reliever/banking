"""Domain-layer error codes — mirror commands.yaml.errors and the schema enums.

Each ``DomainError`` carries the canonical ``code`` declared in
``process/CAP.SUP.002.BEN/commands.yaml`` so the presentation layer can map
directly to the HTTP response without re-stringifying.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainError(Exception):
    """Base class for domain-layer errors.

    The ``code`` is the canonical error code from ``commands.yaml`` (e.g.
    ``IDENTITY_FIELDS_MISSING``). The ``message`` is a human-readable
    explanation.
    """

    code: str
    message: str

    def __str__(self) -> str:  # pragma: no cover — trivial
        return f"{self.code}: {self.message}"


class IdentityFieldsMissing(DomainError):
    """PRE.002 of CMD.MINT_ANCHOR — required identity fields are missing."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            code="IDENTITY_FIELDS_MISSING",
            message=f"Missing required identity fields: {', '.join(missing)}",
        )


class CallerSuppliedInternalId(DomainError):
    """INV.BEN.001 — server is the only legitimate minter of internal_id."""

    def __init__(self) -> None:
        super().__init__(
            code="CALLER_SUPPLIED_INTERNAL_ID",
            message="internal_id is server-minted; the request must not carry one.",
        )


class AnchorNotFound(DomainError):
    """GET / lifecycle commands — no anchor matches the given internal_id."""

    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_NOT_FOUND",
            message=f"No anchor found for internal_id={internal_id}.",
        )


class AnchorAlreadyArchived(DomainError):
    """INV.BEN.004 — ARCHIVE refused; the anchor is already ARCHIVED."""

    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_ALREADY_ARCHIVED",
            message=f"Anchor {internal_id} is already ARCHIVED.",
        )


class AnchorNotArchived(DomainError):
    """INV.BEN.005 — RESTORE refused; the anchor is not ARCHIVED."""

    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_NOT_ARCHIVED",
            message=(
                f"Anchor {internal_id} is not ARCHIVED — nothing to restore."
            ),
        )


class AnchorPseudonymised(DomainError):
    """INV.BEN.007 — PSEUDONYMISED is terminal; lifecycle commands refused."""

    def __init__(self, internal_id: str) -> None:
        super().__init__(
            code="ANCHOR_PSEUDONYMISED",
            message=(
                f"Anchor {internal_id} is PSEUDONYMISED — terminal state, "
                "no further lifecycle command is accepted."
            ),
        )


class InvalidReason(DomainError):
    """ARCHIVE / RESTORE — the `reason` field is missing or outside the
    canonical enum. Normally caught at the schema layer; this is a
    defence-in-depth fallback for handlers invoked without prior schema
    validation (e.g. direct in-process callers in unit tests).
    """

    def __init__(self, scope: str, reason: str | None) -> None:
        super().__init__(
            code="INVALID_REASON",
            message=(
                f"{scope}: reason {reason!r} is missing or outside the "
                "canonical enum."
            ),
        )
