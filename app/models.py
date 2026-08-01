from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator


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


class QualificationReasonCode(StrEnum):
    BUDGET_COVERS_PRICE = "budget.covers_price"
    BUDGET_WITHIN_90_PERCENT = "budget.within_90_percent"
    BUDGET_WITHIN_75_PERCENT = "budget.within_75_percent"
    BUDGET_BELOW_75_PERCENT = "budget.below_75_percent"

    FINANCING_CASH = "financing.cash"
    FINANCING_PRE_APPROVED = "financing.pre_approved"
    FINANCING_NEEDED = "financing.needs_financing"
    FINANCING_UNKNOWN = "financing.unknown"

    TIMEFRAME_WITHIN_1_MONTH = "timeframe.within_1_month"
    TIMEFRAME_WITHIN_3_MONTHS = "timeframe.within_3_months"
    TIMEFRAME_WITHIN_6_MONTHS = "timeframe.within_6_months"
    TIMEFRAME_OVER_6_MONTHS = "timeframe.more_than_6_months"
    TIMEFRAME_UNKNOWN = "timeframe.unknown"

    VISIT_REQUESTED = "visit.requested"
    VISIT_NOT_REQUESTED = "visit.not_requested"


class LeadQualificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maximum_purchase_budget: Decimal = Field(
        gt=0,
        allow_inf_nan=False,
        max_digits=14,
        decimal_places=2,
    )
    property_price: Decimal = Field(
        gt=0,
        allow_inf_nan=False,
        max_digits=14,
        decimal_places=2,
    )
    financing_status: FinancingStatus
    purchase_timeframe: PurchaseTimeframe
    visit_interest: StrictBool


class QualificationReason(BaseModel):
    code: QualificationReasonCode
    message: str
    points: int = Field(ge=0, le=35)


class LeadQualificationResponse(BaseModel):
    policy_version: Literal["v0.2"]
    score: int = Field(ge=0, le=100)
    classification: LeadClassification
    reasons: list[QualificationReason] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def validate_qualification_integrity(self) -> "LeadQualificationResponse":
        expected_reason_prefixes = ("budget.", "financing.", "timeframe.", "visit.")
        actual_reason_codes = tuple(reason.code.value for reason in self.reasons)

        if not all(
            code.startswith(prefix)
            for code, prefix in zip(
                actual_reason_codes,
                expected_reason_prefixes,
                strict=True,
            )
        ):
            raise ValueError(
                "reasons must appear in budget, financing, timeframe, visit order"
            )

        if sum(reason.points for reason in self.reasons) != self.score:
            raise ValueError("reason points must sum to score")

        if self.score >= 70:
            expected_classification = LeadClassification.HOT
        elif self.score >= 35:
            expected_classification = LeadClassification.WARM
        else:
            expected_classification = LeadClassification.COLD

        if self.classification != expected_classification:
            raise ValueError("classification must match score thresholds")

        return self
