"""Pydantic models for the Compliance Assistant MCP server.

Single source of truth for entity shapes and tool-input schemas, matching
specs/mcp-integration-spec.md §4 exactly. Used to both validate mockdata/*.json
at load time and to generate the MCP tool input schemas at registration time
(Pydantic -> JSON Schema is how the `mcp` SDK expects tool inputs to be described).

See CLAUDE.md "Domain data model" and "MCP tool contracts" for the spec this
implements, and ai/DECISIONS.md §23 for why schemas are written before the data.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# --- Enums (SCREAMING_SNAKE_CASE values, per CLAUDE.md naming conventions) ---


class SupplierCategory(str, Enum):
    DAIRY = "DAIRY"
    PRODUCE = "PRODUCE"
    MEAT = "MEAT"
    BAKERY = "BAKERY"
    SEAFOOD = "SEAFOOD"


class RiskRating(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CertificationStandard(str, Enum):
    BRCGS = "BRCGS"
    GLOBALGAP = "GLOBALGAP"
    ISO22000 = "ISO22000"
    SALSA = "SALSA"


class CertificationStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class SpecificationStatus(str, Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"


class Allergen(str, Enum):
    MILK = "MILK"
    EGGS = "EGGS"
    GLUTEN = "GLUTEN"
    PEANUTS = "PEANUTS"
    TREE_NUTS = "TREE_NUTS"
    SOY = "SOY"
    FISH = "FISH"
    SHELLFISH = "SHELLFISH"
    SESAME = "SESAME"


class IncidentType(str, Enum):
    RECALL = "RECALL"
    COMPLAINT = "COMPLAINT"
    NON_CONFORMANCE = "NON_CONFORMANCE"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolErrorType(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"


# --- Entities (CLAUDE.md "Domain data model") ---


class Supplier(BaseModel):
    id: str
    name: str
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    category: SupplierCategory
    risk_rating: RiskRating


class Certification(BaseModel):
    id: str
    supplier_id: str
    standard: CertificationStandard
    status: CertificationStatus
    expiry_date: date


class Specification(BaseModel):
    id: str
    supplier_id: str
    name: str
    category: SupplierCategory
    allergens: list[Allergen] = Field(default_factory=list)
    status: SpecificationStatus


class QualityIncident(BaseModel):
    id: str
    specification_id: str
    date: date
    type: IncidentType
    severity: IncidentSeverity
    description: str = Field(max_length=500)


# --- Shared reasoning field (structural enforcement, specs/agent-spec.md §4) ---
# Every tool input model below inherits this. A missing or whitespace-only
# reasoning must fail Pydantic validation -> the server maps that to
# VALIDATION_ERROR (specs/mcp-integration-spec.md §4 "All five tools require...").


class _ReasoningRequired(BaseModel):
    reasoning: str = Field(min_length=1)

    @field_validator("reasoning")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reasoning must not be blank")
        return v


# --- Tool input models (specs/mcp-integration-spec.md §4) ---


class SearchSuppliersInput(_ReasoningRequired):
    query: str | None = None
    category: SupplierCategory | None = None
    country: str | None = None
    risk_rating: RiskRating | None = None


class GetSupplierProfileInput(_ReasoningRequired):
    supplier_id: str


class SearchSpecificationsInput(_ReasoningRequired):
    query: str | None = None
    supplier_id: str | None = None
    category: SupplierCategory | None = None


class SearchQualityIncidentsInput(_ReasoningRequired):
    specification_id: str | None = None
    supplier_id: str | None = None
    since_date: date | None = None
    type: IncidentType | None = None


class CheckAllergenConflictsInput(_ReasoningRequired):
    specification_id: str
    allergens_to_avoid: list[Allergen] = Field(min_length=1)


# --- Reserved test fixture ID (CLAUDE.md "Deliberate test fixtures") ---

RESERVED_TIMEOUT_SUPPLIER_ID = "SUP-TIMEOUT-01"
