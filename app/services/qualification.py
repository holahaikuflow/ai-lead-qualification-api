from decimal import Decimal

from app.models import (
    FinancingStatus,
    LeadClassification,
    LeadQualificationRequest,
    LeadQualificationResponse,
    PurchaseTimeframe,
    QualificationReason,
    QualificationReasonCode,
)


def score_budget(
    maximum_purchase_budget: Decimal,
    property_price: Decimal,
) -> QualificationReason:
    ratio = maximum_purchase_budget / property_price

    if ratio >= Decimal("1.00"):
        return QualificationReason(
            code=QualificationReasonCode.BUDGET_COVERS_PRICE,
            message="Budget covers the property price.",
            points=35,
        )
    if ratio >= Decimal("0.90"):
        return QualificationReason(
            code=QualificationReasonCode.BUDGET_WITHIN_90_PERCENT,
            message="Budget covers at least 90% of the property price.",
            points=25,
        )
    if ratio >= Decimal("0.75"):
        return QualificationReason(
            code=QualificationReasonCode.BUDGET_WITHIN_75_PERCENT,
            message="Budget covers at least 75% of the property price.",
            points=15,
        )
    return QualificationReason(
        code=QualificationReasonCode.BUDGET_BELOW_75_PERCENT,
        message="Budget covers less than 75% of the property price.",
        points=0,
    )


def score_financing(status: FinancingStatus) -> QualificationReason:
    results = {
        FinancingStatus.CASH: QualificationReason(
            code=QualificationReasonCode.FINANCING_CASH,
            message="Customer can purchase with cash.",
            points=25,
        ),
        FinancingStatus.PRE_APPROVED: QualificationReason(
            code=QualificationReasonCode.FINANCING_PRE_APPROVED,
            message="Financing is pre-approved.",
            points=20,
        ),
        FinancingStatus.NEEDS_FINANCING: QualificationReason(
            code=QualificationReasonCode.FINANCING_NEEDED,
            message="Customer still needs financing.",
            points=5,
        ),
        FinancingStatus.UNKNOWN: QualificationReason(
            code=QualificationReasonCode.FINANCING_UNKNOWN,
            message="Financing status is unknown.",
            points=0,
        ),
    }
    return results[status]


def score_timeframe(timeframe: PurchaseTimeframe) -> QualificationReason:
    results = {
        PurchaseTimeframe.WITHIN_1_MONTH: QualificationReason(
            code=QualificationReasonCode.TIMEFRAME_WITHIN_1_MONTH,
            message="Purchase timeframe is within one month.",
            points=25,
        ),
        PurchaseTimeframe.WITHIN_3_MONTHS: QualificationReason(
            code=QualificationReasonCode.TIMEFRAME_WITHIN_3_MONTHS,
            message="Purchase timeframe is within three months.",
            points=20,
        ),
        PurchaseTimeframe.WITHIN_6_MONTHS: QualificationReason(
            code=QualificationReasonCode.TIMEFRAME_WITHIN_6_MONTHS,
            message="Purchase timeframe is within six months.",
            points=10,
        ),
        PurchaseTimeframe.MORE_THAN_6_MONTHS: QualificationReason(
            code=QualificationReasonCode.TIMEFRAME_OVER_6_MONTHS,
            message="Purchase timeframe is more than six months.",
            points=0,
        ),
        PurchaseTimeframe.UNKNOWN: QualificationReason(
            code=QualificationReasonCode.TIMEFRAME_UNKNOWN,
            message="Purchase timeframe is unknown.",
            points=0,
        ),
    }
    return results[timeframe]


def score_visit(visit_interest: bool) -> QualificationReason:
    if visit_interest:
        return QualificationReason(
            code=QualificationReasonCode.VISIT_REQUESTED,
            message="Customer requested a property visit.",
            points=15,
        )
    return QualificationReason(
        code=QualificationReasonCode.VISIT_NOT_REQUESTED,
        message="Customer has not requested a property visit.",
        points=0,
    )


def classify_score(score: int) -> LeadClassification:
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if score >= 70:
        return LeadClassification.HOT
    if score >= 35:
        return LeadClassification.WARM
    return LeadClassification.COLD


def qualify_lead(lead: LeadQualificationRequest) -> LeadQualificationResponse:
    reasons = [
        score_budget(lead.maximum_purchase_budget, lead.property_price),
        score_financing(lead.financing_status),
        score_timeframe(lead.purchase_timeframe),
        score_visit(lead.visit_interest),
    ]
    score = sum(reason.points for reason in reasons)

    return LeadQualificationResponse(
        policy_version="v0.2",
        score=score,
        classification=classify_score(score),
        reasons=reasons,
    )
