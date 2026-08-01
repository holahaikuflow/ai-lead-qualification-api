from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import (
    FinancingStatus,
    LeadClassification,
    LeadQualificationRequest,
    LeadQualificationResponse,
    PurchaseTimeframe,
    QualificationReasonCode,
)
from app.services.qualification import (
    classify_score,
    qualify_lead,
    score_budget,
    score_financing,
    score_timeframe,
    score_visit,
)


client = TestClient(app)


def valid_payload() -> dict[str, object]:
    return {
        "maximum_purchase_budget": "500000.00",
        "property_price": "500000.00",
        "financing_status": "cash",
        "purchase_timeframe": "within_1_month",
        "visit_interest": True,
    }


@pytest.mark.parametrize(
    ("budget", "price", "points", "code"),
    [
        ("101.00", "100.00", 35, QualificationReasonCode.BUDGET_COVERS_PRICE),
        ("100.00", "100.00", 35, QualificationReasonCode.BUDGET_COVERS_PRICE),
        ("99.99", "100.00", 25, QualificationReasonCode.BUDGET_WITHIN_90_PERCENT),
        ("90.00", "100.00", 25, QualificationReasonCode.BUDGET_WITHIN_90_PERCENT),
        ("89.99", "100.00", 15, QualificationReasonCode.BUDGET_WITHIN_75_PERCENT),
        ("75.00", "100.00", 15, QualificationReasonCode.BUDGET_WITHIN_75_PERCENT),
        ("74.99", "100.00", 0, QualificationReasonCode.BUDGET_BELOW_75_PERCENT),
    ],
)
def test_budget_scoring_boundaries(
    budget: str,
    price: str,
    points: int,
    code: QualificationReasonCode,
) -> None:
    reason = score_budget(Decimal(budget), Decimal(price))

    assert reason.points == points
    assert reason.code == code


@pytest.mark.parametrize(
    ("status", "points", "code"),
    [
        (FinancingStatus.CASH, 25, QualificationReasonCode.FINANCING_CASH),
        (
            FinancingStatus.PRE_APPROVED,
            20,
            QualificationReasonCode.FINANCING_PRE_APPROVED,
        ),
        (
            FinancingStatus.NEEDS_FINANCING,
            5,
            QualificationReasonCode.FINANCING_NEEDED,
        ),
        (FinancingStatus.UNKNOWN, 0, QualificationReasonCode.FINANCING_UNKNOWN),
    ],
)
def test_financing_scoring(
    status: FinancingStatus,
    points: int,
    code: QualificationReasonCode,
) -> None:
    reason = score_financing(status)

    assert reason.points == points
    assert reason.code == code


@pytest.mark.parametrize(
    ("timeframe", "points", "code"),
    [
        (
            PurchaseTimeframe.WITHIN_1_MONTH,
            25,
            QualificationReasonCode.TIMEFRAME_WITHIN_1_MONTH,
        ),
        (
            PurchaseTimeframe.WITHIN_3_MONTHS,
            20,
            QualificationReasonCode.TIMEFRAME_WITHIN_3_MONTHS,
        ),
        (
            PurchaseTimeframe.WITHIN_6_MONTHS,
            10,
            QualificationReasonCode.TIMEFRAME_WITHIN_6_MONTHS,
        ),
        (
            PurchaseTimeframe.MORE_THAN_6_MONTHS,
            0,
            QualificationReasonCode.TIMEFRAME_OVER_6_MONTHS,
        ),
        (
            PurchaseTimeframe.UNKNOWN,
            0,
            QualificationReasonCode.TIMEFRAME_UNKNOWN,
        ),
    ],
)
def test_timeframe_scoring(
    timeframe: PurchaseTimeframe,
    points: int,
    code: QualificationReasonCode,
) -> None:
    reason = score_timeframe(timeframe)

    assert reason.points == points
    assert reason.code == code


@pytest.mark.parametrize(
    ("visit_interest", "points", "code"),
    [
        (True, 15, QualificationReasonCode.VISIT_REQUESTED),
        (False, 0, QualificationReasonCode.VISIT_NOT_REQUESTED),
    ],
)
def test_visit_scoring(
    visit_interest: bool,
    points: int,
    code: QualificationReasonCode,
) -> None:
    reason = score_visit(visit_interest)

    assert reason.points == points
    assert reason.code == code


@pytest.mark.parametrize(
    ("score", "classification"),
    [
        (0, LeadClassification.COLD),
        (34, LeadClassification.COLD),
        (35, LeadClassification.WARM),
        (69, LeadClassification.WARM),
        (70, LeadClassification.HOT),
        (100, LeadClassification.HOT),
    ],
)
def test_classification_boundaries(
    score: int,
    classification: LeadClassification,
) -> None:
    assert classify_score(score) == classification


@pytest.mark.parametrize("score", [-1, 101])
def test_classification_rejects_out_of_range_scores(score: int) -> None:
    with pytest.raises(ValueError, match="score must be between 0 and 100"):
        classify_score(score)


@pytest.mark.parametrize("missing_field", list(valid_payload()))
def test_all_request_fields_are_required(missing_field: str) -> None:
    payload = valid_payload()
    del payload[missing_field]

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 422


def test_empty_request_is_rejected() -> None:
    response = client.post("/api/v1/leads/qualify", json={})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "value",
    [0, -1, "NaN", "Infinity", "-Infinity", "1234567890123.45", "1.234"],
)
@pytest.mark.parametrize(
    "field",
    ["maximum_purchase_budget", "property_price"],
)
def test_invalid_monetary_values_are_rejected(field: str, value: object) -> None:
    payload = valid_payload()
    payload[field] = value

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("value", ["true", "false", 1, 0, None])
def test_visit_interest_requires_a_strict_boolean(value: object) -> None:
    payload = valid_payload()
    payload["visit_interest"] = value

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("financing_status", "approved"),
        ("purchase_timeframe", "tomorrow"),
    ],
)
def test_invalid_enums_are_rejected(field: str, value: str) -> None:
    payload = valid_payload()
    payload[field] = value

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 422


def test_unexpected_fields_are_rejected() -> None:
    payload = valid_payload()
    payload["budget"] = "500000.00"

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 422


def test_response_contract_and_stable_reason_order() -> None:
    lead = LeadQualificationRequest(**valid_payload())

    result = qualify_lead(lead)

    assert result.policy_version == "v0.2"
    assert result.score == 100
    assert result.classification == LeadClassification.HOT
    assert [reason.code for reason in result.reasons] == [
        QualificationReasonCode.BUDGET_COVERS_PRICE,
        QualificationReasonCode.FINANCING_CASH,
        QualificationReasonCode.TIMEFRAME_WITHIN_1_MONTH,
        QualificationReasonCode.VISIT_REQUESTED,
    ]
    assert sum(reason.points for reason in result.reasons) == result.score


def test_repeated_http_responses_are_deterministic() -> None:
    first = client.post("/api/v1/leads/qualify", json=valid_payload())
    second = client.post("/api/v1/leads/qualify", json=valid_payload())

    assert first.status_code == 200
    assert first.json() == second.json()


def test_http_and_service_results_agree() -> None:
    payload = valid_payload()
    service_result = qualify_lead(LeadQualificationRequest(**payload))

    response = client.post("/api/v1/leads/qualify", json=payload)

    assert response.status_code == 200
    assert response.json() == service_result.model_dump(mode="json")


def test_request_model_rejects_extra_fields_at_service_boundary() -> None:
    with pytest.raises(ValidationError):
        LeadQualificationRequest(**valid_payload(), extra_field="unexpected")


def valid_response_data() -> dict[str, object]:
    result = qualify_lead(LeadQualificationRequest(**valid_payload()))
    return result.model_dump()


def test_response_rejects_invalid_reason_order() -> None:
    response_data = valid_response_data()
    reasons = response_data["reasons"]
    assert isinstance(reasons, list)
    reasons[0], reasons[1] = reasons[1], reasons[0]

    with pytest.raises(ValidationError, match="budget, financing, timeframe, visit"):
        LeadQualificationResponse.model_validate(response_data)


def test_response_rejects_reason_points_not_matching_score() -> None:
    response_data = valid_response_data()
    response_data["score"] = 99

    with pytest.raises(ValidationError, match="reason points must sum to score"):
        LeadQualificationResponse.model_validate(response_data)


def test_response_rejects_classification_not_matching_score() -> None:
    response_data = valid_response_data()
    response_data["classification"] = LeadClassification.COLD

    with pytest.raises(ValidationError, match="classification must match score"):
        LeadQualificationResponse.model_validate(response_data)
