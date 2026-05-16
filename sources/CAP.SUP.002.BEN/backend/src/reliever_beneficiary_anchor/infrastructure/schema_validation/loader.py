"""Load canonical JSON Schemas from the read-only process/ folder.

The schemas are the source of truth — this service is a *consumer* of them.
Fail-fast at startup if any schema is missing or malformed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

from ...application.ports import SchemaValidator


# Resolved at startup from settings.PROCESS_SCHEMAS_DIR.
MINT_ANCHOR_SCHEMA_FILE = "CMD.SUP.002.BEN.MINT_ANCHOR.schema.json"
RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE = "RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED.schema.json"


class JsonSchemaValidator(SchemaValidator):
    def __init__(self, schema: dict[str, Any]) -> None:
        # Will raise SchemaError on a malformed schema — fail-fast.
        Draft202012Validator.check_schema(schema)
        self._validator = Draft202012Validator(
            schema,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )

    def validate_payload(self, payload: dict[str, Any]) -> None:
        self._validator.validate(payload)


def load_schema(schemas_dir: Path, filename: str) -> dict[str, Any]:
    path = schemas_dir / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Required process-layer schema not found: {path}. "
            "This service is a read-only consumer of process/CAP.SUP.002.BEN/schemas/."
        )
    with path.open() as f:
        return json.load(f)


def build_validators(schemas_dir: Path) -> tuple[JsonSchemaValidator, JsonSchemaValidator]:
    """Return (mint_cmd_validator, rvt_validator). Fail-fast on any issue."""
    mint = load_schema(schemas_dir, MINT_ANCHOR_SCHEMA_FILE)
    rvt = load_schema(schemas_dir, RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE)
    return JsonSchemaValidator(mint), JsonSchemaValidator(rvt)


__all__ = [
    "JsonSchemaValidator",
    "build_validators",
    "MINT_ANCHOR_SCHEMA_FILE",
    "RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE",
]
