"""
backend/models/schemas.py
==========================
PURPOSE:
    Pydantic models for all HTTP request bodies and response payloads.
    These are the "shapes" of data that flow through the API layer.

ARCHITECTURE ROLE:
    Schemas sit at the API boundary — they validate incoming requests and
    serialise outgoing responses. They are SEPARATE from db_models.py
    (which describes database rows) because:
        - API shapes often differ from DB shapes (e.g. nested objects in response
          vs flat rows in DB)
        - Pydantic models provide automatic validation + clear error messages
        - TypedDicts (in db_models.py) are for DB rows; BaseModel is for HTTP

DESIGN DECISION — APIEnvelope:
    All API responses are wrapped in a consistent envelope:
        Success: {"data": <payload>, "error": null}
        Failure: {"data": null, "error": {"code": "...", "message": "..."}}

    WHY AN ENVELOPE?
        Without an envelope, clients must check HTTP status codes AND parse
        different response body shapes for success vs error. With an envelope,
        clients always get the same structure — they check `error` first,
        then read `data`. This is the pattern used by Stripe, Twilio, and
        most production APIs. (Requirement 5.3)
"""

# Generic: enables APIEnvelope[T] to be typed with any T (TypeVar)
# TypeVar: defines T as a placeholder type variable
from typing import Generic, TypeVar, Optional, Any

# datetime: type hint for timestamp fields
from datetime import datetime

# BaseModel: Pydantic base class — validates field types and required/optional
# Field: adds metadata like description, examples, constraints to fields
from pydantic import BaseModel, Field

# TypeVar T — a placeholder that says "this field can be any type".
# When we write APIEnvelope[TransactionResponse], T becomes TransactionResponse.
T = TypeVar("T")


# =============================================================================
# SHARED / UTILITY SCHEMAS
# =============================================================================

class ErrorDetail(BaseModel):
    """
    Structured error information included in failed API responses.

    Attributes:
        code:    Machine-readable error code (e.g. "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable explanation of what went wrong.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")


class APIEnvelope(BaseModel, Generic[T]):
    """
    Universal response wrapper for all API endpoints. (Requirement 5.3)

    Every successful response:   {"data": <payload>, "error": null}
    Every error response:        {"data": null, "error": {"code": ..., "message": ...}}

    The Generic[T] means the `data` field can hold ANY type — the caller
    specifies it: APIEnvelope[TransactionResponse], APIEnvelope[list[AlertResponse]], etc.

    Attributes:
        data:  The response payload on success, null on error.
        error: Error details on failure, null on success.
    """
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def success(cls, data: T) -> "APIEnvelope[T]":
        """Convenience constructor for successful responses."""
        return cls(data=data, error=None)

    @classmethod
    def failure(cls, code: str, message: str) -> "APIEnvelope":
        """Convenience constructor for error responses."""
        return cls(data=None, error=ErrorDetail(code=code, message=message))


class PaginatedList(BaseModel, Generic[T]):
    """
    Wrapper for paginated list responses.

    Attributes:
        items:      The list of items on the current page.
        total:      Total number of items across all pages.
        page:       Current page number (1-based).
        page_size:  Number of items per page.
        has_more:   True if there are more pages after this one.
    """
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# ML INFERENCE SCHEMAS
# =============================================================================

class FeatureContribution(BaseModel):
    """
    One SHAP feature contribution explaining why a fraud score is high/low.

    Example: {"feature": "amount_zscore", "contribution": 0.42}
    Positive contribution = pushed score toward fraud.
    Negative contribution = pushed score away from fraud.
    """
    feature: str = Field(..., description="Feature name (e.g. 'amount_zscore')")
    contribution: float = Field(..., description="SHAP contribution value — positive = toward fraud")


# =============================================================================
# TRANSACTION SCHEMAS
# =============================================================================

class TransactionRequest(BaseModel):
    """
    Request body for POST /transactions.

    Submitted by the simulation script or external callers when a new
    transaction needs to be scored. All fields are validated by Pydantic
    before the handler runs. (Requirement 2.5, 5.2)
    """
    amount: float = Field(..., gt=0, description="Transaction amount, must be > 0")
    currency: str = Field(default="USD", min_length=3, max_length=3,
                          description="ISO 4217 currency code (e.g. 'USD')")
    merchant_name: str = Field(..., min_length=1, description="Merchant display name")
    merchant_category: str = Field(..., min_length=1, description="Merchant category (e.g. 'electronics')")
    card_last_four: str = Field(..., min_length=4, max_length=4,
                                description="Last 4 digits of the card")
    cardholder_name: str = Field(..., min_length=1, description="Name on the card")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90,
                                      description="GPS latitude of transaction")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180,
                                       description="GPS longitude of transaction")
    description: Optional[str] = Field(default=None, description="Human-readable purchase description")

    # Derived features computed from the request context (set by the router,
    # not by the caller — the caller doesn't know these values)
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23,
                                       description="Hour of submission (0-23)")
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6,
                                       description="Day of week (0=Monday)")


class TransactionResponse(BaseModel):
    """
    Response body for GET /transactions/{id} and the result of POST /transactions.

    Contains the full transaction data including ML scoring output.
    Nested `alert` and `report` fields are included when they exist.
    """
    model_config = {"protected_namespaces": ()}

    id: str
    amount: float
    currency: str
    merchant_name: str
    merchant_category: str
    card_last_four: str
    cardholder_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

    # ML scoring output
    fraud_score: Optional[float] = None
    top_features: list[FeatureContribution] = []
    model_name: Optional[str] = None

    # Status
    is_fraud: bool
    status: str

    # Timestamps
    submitted_at: str
    scored_at: Optional[str] = None

    # Nested related objects (included when fetching by ID)
    alert: Optional["AlertSummary"] = None
    report: Optional["ReportSummary"] = None


# =============================================================================
# ALERT SCHEMAS
# =============================================================================

class AlertSummary(BaseModel):
    """
    Compact alert summary nested inside TransactionResponse.
    Contains just enough info to show the alert status without the full report.
    """
    id: str
    status: str
    fraud_score: float
    created_at: str


class AlertResponse(BaseModel):
    """
    Full alert response for GET /alerts/{id}.
    Includes the nested full report when the investigation is complete.
    """
    id: str
    transaction_id: str
    threshold_at_creation: float
    fraud_score: float
    status: str
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None

    # Nested full report — None if investigation hasn't started yet
    report: Optional["ReportResponse"] = None


# =============================================================================
# REPORT SCHEMAS
# =============================================================================

class InvestigationStep(BaseModel):
    """
    One step in the LangChain ReAct reasoning loop.
    Rendered as a card in the ReasoningTrace UI component.
    """
    step_number: int
    step_type: str              # "thought" | "action" | "observation" | "final_answer"
    tool_name: Optional[str] = None
    tool_input: Optional[Any] = None
    tool_output: Optional[Any] = None
    content: Optional[str] = None
    is_error: bool = False
    error_detail: Optional[str] = None


class ReportSummary(BaseModel):
    """
    Compact report summary nested inside AlertResponse and TransactionResponse.
    Shows verdict/confidence without the full reasoning trace.
    """
    id: str
    verdict: str
    confidence: str
    status: str
    completed_at: Optional[str] = None


class ReportResponse(BaseModel):
    """
    Full report response for GET /reports/{id}.
    Includes the complete reasoning_trace list of all investigation steps.
    This is what the ReasoningTrace UI component renders. (Requirement 3.3, 3.4)
    """
    id: str
    alert_id: str

    # Agent verdict
    verdict: str                                    # "fraudulent" | "suspicious" | "legitimate"
    confidence: str                                 # "high" | "medium" | "low"
    explanation: str                                # plain-English reasoning
    recommended_actions: list[str] = []
    clarifying_questions: list[str] = []           # up to 3 (Requirement 3.8)

    # Full step-by-step reasoning trace
    reasoning_trace: list[InvestigationStep] = []

    # Lifecycle
    status: str
    error_message: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None


# =============================================================================
# ANALYTICS SCHEMAS
# =============================================================================

class DailyDataPoint(BaseModel):
    """One day's worth of transaction + alert counts for the time-series chart."""
    date: str           # "YYYY-MM-DD" format
    transactions: int
    alerts: int


class FraudSignalCategory(BaseModel):
    """Top fraud-generating merchant category with its count."""
    category: str
    count: int


class AnalyticsSummary(BaseModel):
    """
    Response for GET /analytics/summary.
    Powers all four panels of the dashboard analytics section. (Requirement 7.4)
    """
    model_config = {"protected_namespaces": ()}

    total_transactions_today: int
    fraud_rate_today: float                         # 0.0-1.0 (e.g. 0.043 = 4.3%)
    total_alerts_open: int
    alert_resolution_rate: float                    # fraction of alerts resolved
    model_accuracy: float                           # AUC-ROC from training log
    top_fraud_signal_categories: list[FraudSignalCategory]
    daily_series: list[DailyDataPoint]              # last 7 days


# Forward-reference resolution — needed for nested models that reference each other
TransactionResponse.model_rebuild()
AlertResponse.model_rebuild()
