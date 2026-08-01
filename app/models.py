from enum import StrEnum

from pydantic import BaseModel, Field


class FinancingStatus(StrEnum):
    CASH = "cash"
    PRE_APPROVED = "pre_approved"
    NEEDS_FINANCING = "needs_financing"
    UNKNOWN = "unknown"


class PurchaseTimeframe(StrEnum):
    WITHIN_1_MONTH = "within_1_month"
    WITHIN_3_MONTHS = "within_3_months"
    WITHIN_6_MONTHS = "within_6_months"
    MORE_THAN_6_MONTHS = "more_than_6_months"
    UNKNOWN = "unknown"


class LeadClassification(StrEnum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class LeadQualificationRequest(BaseModel):
    budget: float | None = Field(default=None, gt=0)
    financing_status: FinancingStatus = FinancingStatus.UNKNOWN
    purchase_timeframe: PurchaseTimeframe = PurchaseTimeframe.UNKNOWN
    visit_interest: bool = False


class LeadQualificationResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    classification: LeadClassification
    reasons: list[str]
