from app.models import (
    FinancingStatus,
    LeadClassification,
    LeadQualificationRequest,
    LeadQualificationResponse,
    PurchaseTimeframe,
)


def qualify_lead(lead: LeadQualificationRequest) -> LeadQualificationResponse:
    score = 0
    reasons: list[str] = []

    if lead.financing_status == FinancingStatus.CASH:
        score += 35
        reasons.append("Customer can purchase with cash")
    elif lead.financing_status == FinancingStatus.PRE_APPROVED:
        score += 30
        reasons.append("Financing is pre-approved")
    elif lead.financing_status == FinancingStatus.NEEDS_FINANCING:
        score += 10
        reasons.append("Customer still needs financing")

    if lead.purchase_timeframe == PurchaseTimeframe.WITHIN_1_MONTH:
        score += 35
        reasons.append("Purchase timeframe is within one month")
    elif lead.purchase_timeframe == PurchaseTimeframe.WITHIN_3_MONTHS:
        score += 25
        reasons.append("Purchase timeframe is within three months")
    elif lead.purchase_timeframe == PurchaseTimeframe.WITHIN_6_MONTHS:
        score += 15
        reasons.append("Purchase timeframe is within six months")

    if lead.visit_interest:
        score += 30
        reasons.append("Customer requested a visit")

    score = min(score, 100)

    if score >= 70:
        classification = LeadClassification.HOT
    elif score >= 35:
        classification = LeadClassification.WARM
    else:
        classification = LeadClassification.COLD

    return LeadQualificationResponse(
        score=score,
        classification=classification,
        reasons=reasons,
    )
