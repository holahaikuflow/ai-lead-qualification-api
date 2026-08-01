from app.models import (
    FinancingStatus,
    LeadClassification,
    LeadQualificationRequest,
    PurchaseTimeframe,
)
from app.services.qualification import qualify_lead


def test_hot_lead() -> None:
    lead = LeadQualificationRequest(
        budget=120000,
        financing_status=FinancingStatus.PRE_APPROVED,
        purchase_timeframe=PurchaseTimeframe.WITHIN_3_MONTHS,
        visit_interest=True,
    )

    result = qualify_lead(lead)

    assert result.score == 85
    assert result.classification == LeadClassification.HOT
    assert result.reasons == [
        "Financing is pre-approved",
        "Purchase timeframe is within three months",
        "Customer requested a visit",
    ]


def test_qualification_endpoint() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/api/v1/leads/qualify",
        json={
            "budget": 120000,
            "financing_status": "pre_approved",
            "purchase_timeframe": "within_3_months",
            "visit_interest": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "score": 85,
        "classification": "hot",
        "reasons": [
            "Financing is pre-approved",
            "Purchase timeframe is within three months",
            "Customer requested a visit",
        ],
    }
