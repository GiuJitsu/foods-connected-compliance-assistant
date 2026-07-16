"""Compliance Assistant MCP Server.

Exposes the 5 read-only tools defined in specs/mcp-integration-spec.md over the
static mock dataset in mockdata/. Transport: stdio (the backend spawns this as
a subprocess — specs/mcp-integration-spec.md §2).

Every tool requires a `reasoning` argument (specs/agent-spec.md §4 — structural
enforcement, not a system-prompt-only request). A missing/blank reasoning, or
any other schema violation, returns a structured VALIDATION_ERROR rather than
raising — tool errors are always a normal result the caller can inspect, never
an uncaught exception (specs/mcp-integration-spec.md §5/§9).
"""

from __future__ import annotations

import json
from pathlib import Path
from time import sleep

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from schemas import (
    RESERVED_TIMEOUT_SUPPLIER_ID,
    Certification,
    CheckAllergenConflictsInput,
    GetSupplierProfileInput,
    QualityIncident,
    SearchQualityIncidentsInput,
    SearchSpecificationsInput,
    SearchSuppliersInput,
    Specification,
    Supplier,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "mockdata"

# Deliberately longer than the backend's 10s per-call timeout
# (CLAUDE.md "Loop bounds") so this reliably trips a real client-side timeout
# rather than racing it.
SIMULATED_TIMEOUT_SECONDS = 12

mcp = FastMCP("foods-connected-compliance-mcp")


def _load(filename: str, model):
    raw = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    return [model.model_validate(record) for record in raw]


SUPPLIERS: list[Supplier] = _load("suppliers.json", Supplier)
CERTIFICATIONS: list[Certification] = _load("certifications.json", Certification)
SPECIFICATIONS: list[Specification] = _load("specifications.json", Specification)
INCIDENTS: list[QualityIncident] = _load("quality_incidents.json", QualityIncident)


def _validation_error(exc: ValidationError) -> dict:
    first = exc.errors()[0]
    field = ".".join(str(p) for p in first["loc"]) or "input"
    return {"error": "VALIDATION_ERROR", "field": field, "message": first["msg"]}


def _not_found(kind: str, entity_id: str, id_field: str) -> dict:
    return {"error": "NOT_FOUND", "message": f"{kind} {entity_id} not found", id_field: entity_id}


@mcp.tool()
def search_suppliers(
    reasoning: str,
    query: str | None = None,
    category: str | None = None,
    country: str | None = None,
    risk_rating: str | None = None,
) -> dict:
    """Find suppliers matching optional filters.

    category: one of DAIRY, PRODUCE, MEAT, BAKERY, SEAFOOD.
    country: ISO 3166-1 alpha-2 code (e.g. "IT", "GB").
    risk_rating: one of LOW, MEDIUM, HIGH.
    reasoning: required — briefly state why this call is being made.
    Returns up to 20 matching suppliers; no matches is a normal empty result, not an error.
    """
    try:
        params = SearchSuppliersInput(
            reasoning=reasoning, query=query, category=category, country=country, risk_rating=risk_rating
        )
    except ValidationError as exc:
        return _validation_error(exc)

    results = SUPPLIERS
    if params.query:
        q = params.query.lower()
        results = [s for s in results if q in s.name.lower()]
    if params.category:
        results = [s for s in results if s.category == params.category]
    if params.country:
        results = [s for s in results if s.country.upper() == params.country.upper()]
    if params.risk_rating:
        results = [s for s in results if s.risk_rating == params.risk_rating]

    results = results[:20]
    return {"results": [s.model_dump(mode="json") for s in results], "count": len(results)}


@mcp.tool()
def get_supplier_profile(reasoning: str, supplier_id: str) -> dict:
    """Full profile for one supplier: its details plus all its certifications.

    reasoning: required — briefly state why this call is being made.
    Unknown supplier_id returns a NOT_FOUND error, never a fabricated/empty-looking record.
    A supplier with zero certifications is a valid, normal result (empty certifications list).
    """
    try:
        params = GetSupplierProfileInput(reasoning=reasoning, supplier_id=supplier_id)
    except ValidationError as exc:
        return _validation_error(exc)

    if params.supplier_id == RESERVED_TIMEOUT_SUPPLIER_ID:
        # Deliberate test fixture — CLAUDE.md "Deliberate test fixtures" / specs/mcp-integration-spec.md §4.
        sleep(SIMULATED_TIMEOUT_SECONDS)

    supplier = next((s for s in SUPPLIERS if s.id == params.supplier_id), None)
    if supplier is None:
        return _not_found("Supplier", params.supplier_id, "supplier_id")

    certs = [c for c in CERTIFICATIONS if c.supplier_id == params.supplier_id]
    return {
        "supplier": supplier.model_dump(mode="json"),
        "certifications": [c.model_dump(mode="json") for c in certs],
    }


@mcp.tool()
def search_specifications(
    reasoning: str,
    query: str | None = None,
    supplier_id: str | None = None,
    category: str | None = None,
) -> dict:
    """Find product specifications matching optional filters.

    category: one of DAIRY, PRODUCE, MEAT, BAKERY, SEAFOOD.
    reasoning: required — briefly state why this call is being made.
    No matches (including an unknown supplier_id used as a filter) is a normal empty result.
    """
    try:
        params = SearchSpecificationsInput(
            reasoning=reasoning, query=query, supplier_id=supplier_id, category=category
        )
    except ValidationError as exc:
        return _validation_error(exc)

    results = SPECIFICATIONS
    if params.query:
        q = params.query.lower()
        results = [s for s in results if q in s.name.lower()]
    if params.supplier_id:
        results = [s for s in results if s.supplier_id == params.supplier_id]
    if params.category:
        results = [s for s in results if s.category == params.category]

    return {"results": [s.model_dump(mode="json") for s in results], "count": len(results)}


@mcp.tool()
def search_quality_incidents(
    reasoning: str,
    specification_id: str | None = None,
    supplier_id: str | None = None,
    since_date: str | None = None,
    type: str | None = None,
) -> dict:
    """Find quality incidents (recalls, complaints, non-conformances) matching optional filters.

    since_date: ISO 8601 date (YYYY-MM-DD) — only incidents on/after this date.
    type: one of RECALL, COMPLAINT, NON_CONFORMANCE.
    reasoning: required — briefly state why this call is being made.
    No matches is a normal empty result — report "no incidents found," never invent one.
    """
    try:
        params = SearchQualityIncidentsInput(
            reasoning=reasoning,
            specification_id=specification_id,
            supplier_id=supplier_id,
            since_date=since_date,
            type=type,
        )
    except ValidationError as exc:
        return _validation_error(exc)

    results = INCIDENTS
    if params.specification_id:
        results = [i for i in results if i.specification_id == params.specification_id]
    if params.supplier_id:
        spec_ids = {s.id for s in SPECIFICATIONS if s.supplier_id == params.supplier_id}
        results = [i for i in results if i.specification_id in spec_ids]
    if params.since_date:
        results = [i for i in results if i.date >= params.since_date]
    if params.type:
        results = [i for i in results if i.type == params.type]

    return {"results": [i.model_dump(mode="json") for i in results], "count": len(results)}


@mcp.tool()
def check_allergen_conflicts(reasoning: str, specification_id: str, allergens_to_avoid: list[str]) -> dict:
    """Check whether a specification's allergens overlap with a caller-supplied avoid-list.

    allergens_to_avoid: non-empty list of allergens, e.g. ["MILK", "GLUTEN"]. One of MILK, EGGS,
    GLUTEN, PEANUTS, TREE_NUTS, SOY, FISH, SHELLFISH, SESAME.
    reasoning: required — briefly state why this call is being made.
    Unknown specification_id returns NOT_FOUND, never a false has_conflict: false.
    """
    try:
        params = CheckAllergenConflictsInput(
            reasoning=reasoning, specification_id=specification_id, allergens_to_avoid=allergens_to_avoid
        )
    except ValidationError as exc:
        return _validation_error(exc)

    spec = next((s for s in SPECIFICATIONS if s.id == params.specification_id), None)
    if spec is None:
        return _not_found("Specification", params.specification_id, "specification_id")

    conflicts = [a for a in spec.allergens if a in params.allergens_to_avoid]
    return {
        "specification_id": spec.id,
        "conflicts": [a.value for a in conflicts],
        "has_conflict": len(conflicts) > 0,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
