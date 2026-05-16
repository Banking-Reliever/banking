"""Pydantic models for the HTTP request/response bodies.

These mirror the JSON Schema canonical shape; the JSON Schema validation
remains the authoritative check (it catches things Pydantic doesn't, like
the conditional ``allOf`` branches on the RVT). Pydantic gives the
FastAPI OpenAPI doc its body shapes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PostalAddressModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line1: str | None = None
    line2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None


class ContactDetailsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    phone: str | None = None
    postal_address: PostalAddressModel | None = None


class MintAnchorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_request_id: str = Field(
        ...,
        description="UUIDv7 — caller-supplied idempotency anchor (30-day window).",
    )
    last_name: str = Field(..., min_length=1, max_length=200)
    first_name: str = Field(..., min_length=1, max_length=200)
    date_of_birth: date
    contact_details: ContactDetailsModel | None = None


class ArchiveAnchorRequest(BaseModel):
    """POST /anchors/{internal_id}/archive body. ``internal_id`` is the
    path parameter — not part of the body."""

    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(
        ...,
        description="UUIDv7 — caller-supplied idempotency anchor (30-day window).",
    )
    reason: str = Field(
        ...,
        description=(
            "Canonical archival reason. One of: PROGRAMME_EXIT_SUCCESS, "
            "PROGRAMME_EXIT_DROPOUT, PROGRAMME_EXIT_TRANSFER, "
            "ADMINISTRATIVE_ARCHIVAL."
        ),
    )
    comment: str | None = Field(default=None, max_length=1000)


class RestoreAnchorRequest(BaseModel):
    """POST /anchors/{internal_id}/restore body. ``internal_id`` is the
    path parameter — not part of the body."""

    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(
        ...,
        description="UUIDv7 — caller-supplied idempotency anchor (30-day window).",
    )
    reason: str = Field(
        ...,
        description=(
            "Canonical restore reason. One of: ARCHIVED_IN_ERROR, "
            "REINSTATED_AFTER_REVIEW."
        ),
    )
    comment: str | None = Field(default=None, max_length=1000)


class BeneficiaryAnchorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    internal_id: str
    last_name: str | None
    first_name: str | None
    date_of_birth: date | None
    contact_details: dict[str, Any] | None
    anchor_status: str
    creation_date: date
    pseudonymized_at: datetime | None
    revision: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    anchor: BeneficiaryAnchorResponse | None = None  # populated for idempotent replay
