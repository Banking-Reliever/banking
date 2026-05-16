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
