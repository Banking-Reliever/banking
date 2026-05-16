"""FastAPI routers — wire the api.yaml contract literally.

api_binding alignment:
  POST  /anchors                — CMD.MINT_ANCHOR
  GET   /anchors/{internal_id}  — QRY.GET_ANCHOR
  GET   /health                 — liveness
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import jsonschema
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from ..application.dto import MintAnchorCommandDto
from ..application.handlers import GetAnchorHandler, MintAnchorHandler, MintResult
from ..domain.errors import (
    AnchorNotFound,
    CallerSuppliedInternalId,
    DomainError,
    IdentityFieldsMissing,
)
from ..domain.value_objects import ContactDetails, PostalAddress
from ..infrastructure.persistence.projection import compute_etag
from ..infrastructure.security.jwt import actor_from_bearer
from .dependencies import AppState, get_state
from .dto import (
    BeneficiaryAnchorResponse,
    ContactDetailsModel,
    ErrorResponse,
    MintAnchorRequest,
)

log = structlog.get_logger()
router = APIRouter()

# RFC-9562 §5.7 — UUIDv7 regex; aligned with the JSON Schema $defs/Uuidv7.
_UUIDV7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


# ─── Health ────────────────────────────────────────────────────────────


@router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ─── CMD.MINT_ANCHOR ───────────────────────────────────────────────────


@router.post(
    "/anchors",
    tags=["commands"],
    summary="Mint a new beneficiary identity anchor",
    response_model=None,
    responses={
        201: {"model": BeneficiaryAnchorResponse, "description": "Anchor minted."},
        200: {
            "model": BeneficiaryAnchorResponse,
            "description": "Idempotent re-call — returns the original anchor (REQUEST_ALREADY_PROCESSED).",
        },
        400: {"model": ErrorResponse, "description": "IDENTITY_FIELDS_MISSING or schema violation."},
    },
)
async def mint_anchor(
    body: dict[str, Any],
    request: Request,
    authorization: str | None = Header(default=None),
    state: AppState = Depends(get_state),
) -> Response:
    # ─── INV.BEN.001 — reject caller-supplied internal_id ──────────────
    if "internal_id" in body:
        raise CallerSuppliedInternalId()

    # ─── JSON Schema validation (canonical contract) ───────────────────
    try:
        state.mint_validator.validate_payload(body)
    except jsonschema.ValidationError as exc:
        # Map the schema error to the canonical IDENTITY_FIELDS_MISSING
        # code when the failure is on a required identity field; otherwise
        # surface a generic INVALID_PAYLOAD.
        missing = [str(p) for p in exc.path]
        msg = exc.message
        # ``required`` violations have an empty path; sniff the message
        # for the missing-field name to map to IDENTITY_FIELDS_MISSING.
        identity_fields = {"last_name", "first_name", "date_of_birth"}
        if exc.validator == "required":
            tokens = re.findall(r"'(\w+)'", msg)
            missing = [t for t in tokens if t in identity_fields]
            if missing:
                err = IdentityFieldsMissing(missing)
                return JSONResponse(
                    status_code=400,
                    content={"error_code": err.code, "message": err.message},
                )
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_PAYLOAD", "message": msg},
        )

    # ─── Pydantic parse (typed shape) ──────────────────────────────────
    try:
        req = MintAnchorRequest.model_validate(body)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=400,
            content={"error_code": "INVALID_PAYLOAD", "message": str(exc)},
        )

    # ─── Build the command DTO ────────────────────────────────────────
    contact = _to_domain_contact(req.contact_details)
    actor = actor_from_bearer(authorization)
    cmd = MintAnchorCommandDto(
        client_request_id=req.client_request_id,
        last_name=req.last_name,
        first_name=req.first_name,
        date_of_birth=req.date_of_birth,
        contact_details=contact,
        actor=actor,
    )

    # ─── Handle ────────────────────────────────────────────────────────
    try:
        result: MintResult = await state.mint_handler.handle(cmd)
    except IdentityFieldsMissing as exc:
        return JSONResponse(
            status_code=400,
            content={"error_code": exc.code, "message": exc.message},
        )

    payload = result.anchor.to_dict()
    if result.idempotent_replay:
        body_out = {"error_code": result.error_code, "anchor": payload}
        return JSONResponse(status_code=200, content=body_out)
    return JSONResponse(status_code=201, content=payload)


def _to_domain_contact(model: ContactDetailsModel | None) -> ContactDetails | None:
    if model is None:
        return None
    postal = model.postal_address
    return ContactDetails(
        email=model.email,
        phone=model.phone,
        postal_address=PostalAddress(
            line1=postal.line1,
            line2=postal.line2,
            postal_code=postal.postal_code,
            city=postal.city,
            country=postal.country,
        ) if postal else None,
    )


# ─── QRY.GET_ANCHOR ────────────────────────────────────────────────────


@router.get(
    "/anchors/{internal_id}",
    tags=["queries"],
    summary="Get an anchor by internal_id",
    response_model=None,
    responses={
        200: {"model": BeneficiaryAnchorResponse},
        304: {"description": "ETag match — body omitted."},
        404: {"model": ErrorResponse, "description": "ANCHOR_NOT_FOUND."},
    },
)
async def get_anchor(
    internal_id: str,
    if_none_match: str | None = Header(default=None),
    state: AppState = Depends(get_state),
) -> Response:
    if not _UUIDV7_RE.match(internal_id):
        # An ill-formed id maps to ANCHOR_NOT_FOUND per the api.yaml contract
        # (we don't expose 422 because the caller can't usefully retry).
        return JSONResponse(
            status_code=404,
            content={"error_code": "ANCHOR_NOT_FOUND",
                     "message": f"No anchor found for internal_id={internal_id}."},
        )

    try:
        dto = await state.get_handler.handle(internal_id)
    except AnchorNotFound as exc:
        return JSONResponse(
            status_code=404,
            content={"error_code": exc.code, "message": exc.message},
        )

    etag = compute_etag(dto.internal_id, dto.revision)
    if if_none_match is not None and _etag_matches(if_none_match, etag):
        # 304 — body omitted but ETag and Cache-Control still set so the
        # client can refresh its TTL.
        return Response(
            status_code=304,
            headers={"ETag": etag, "Cache-Control": "max-age=60"},
        )
    return JSONResponse(
        status_code=200,
        content=dto.to_dict(),
        headers={"ETag": etag, "Cache-Control": "max-age=60"},
    )


def _etag_matches(if_none_match: str, our_etag: str) -> bool:
    """RFC-7232 weak ETag comparison — strip ``W/`` and compare opaque
    values for any of the comma-separated ETags carried by the header.
    """
    def _normalise(t: str) -> str:
        t = t.strip()
        if t.startswith("W/"):
            t = t[2:]
        return t.strip()

    ours = _normalise(our_etag)
    return any(_normalise(t) == ours for t in if_none_match.split(","))


# ─── Domain error handler — uncaught ``DomainError`` → 500 with code ──


def install_exception_handlers(app) -> None:  # noqa: ANN001
    @app.exception_handler(CallerSuppliedInternalId)
    async def _h_caller(_: Request, exc: CallerSuppliedInternalId):
        return JSONResponse(
            status_code=400,
            content={"error_code": exc.code, "message": exc.message},
        )

    @app.exception_handler(DomainError)
    async def _h_domain(_: Request, exc: DomainError):
        log.warning("domain.error", code=exc.code)
        return JSONResponse(
            status_code=400,
            content={"error_code": exc.code, "message": exc.message},
        )
