# AI Lead Qualification API

A deterministic and auditable lead-scoring service built with FastAPI, Pydantic, and Python. It converts validated real-estate purchase signals into a score from 0 to 100, a cold/warm/hot classification, and a structured explanation of the result.

## Live API

The API is deployed on Render.

- [Swagger documentation](https://ai-lead-qualification-api.onrender.com/docs)
- [Health endpoint](https://ai-lead-qualification-api.onrender.com/health)

The free Render instance may sleep after inactivity. The first request after inactivity may take around 50 seconds or more.

### Try it

```bash
curl -X POST https://ai-lead-qualification-api.onrender.com/api/v1/leads/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "maximum_purchase_budget": 450000,
    "property_price": 500000,
    "financing_status": "needs_financing",
    "purchase_timeframe": "within_3_months",
    "visit_interest": false
  }'
```

The expected classification is `warm`.

## Why this project exists

Lead qualification is often embedded inside prompts, conversational flows, or application code where its behavior is difficult to test and audit. This project extracts that responsibility into a small, independently testable service with an explicit API contract.

The design is inspired by a real production real-estate conversational system. In that type of system, an LLM can interpret a customer's natural-language answers, but it should not silently decide business policy. This API establishes a clear boundary:

- An optional upstream interpretation layer turns conversation into structured fields.
- This service validates those fields and applies fixed business rules.
- Every result can be reproduced and explained from the submitted data.

The repository is an implementation-focused portfolio project. It demonstrates production-oriented boundaries and testing practices and includes a publicly deployed demo.

## Current capabilities

- FastAPI HTTP API with generated OpenAPI documentation
- Strict Pydantic request and response validation
- Decimal-based monetary comparison for budget fit
- Deterministic scoring from 0 to 100
- Cold, warm, and hot lead classifications
- Structured reason codes, human-readable messages, and awarded points
- Stable response invariants for reason count, order, point totals, and classification
- Automated tests for scoring branches, boundaries, validation, determinism, and API/service agreement

## Architecture

```text
HTTP request
    → FastAPI endpoint
    → Pydantic validation
    → qualification service
    → structured response
```

The FastAPI layer handles transport, Pydantic defines the contract, and the qualification service contains small pure functions for each scoring dimension. The service has no database or external runtime dependency.

## API endpoints

### `GET /health`

Returns a basic liveness response:

```json
{
  "status": "ok"
}
```

### `POST /api/v1/leads/qualify`

Validates a lead and applies qualification policy `v0.2`.

Valid request:

```json
{
  "maximum_purchase_budget": "500000.00",
  "property_price": "500000.00",
  "financing_status": "cash",
  "purchase_timeframe": "within_1_month",
  "visit_interest": true
}
```

Complete response:

```json
{
  "policy_version": "v0.2",
  "score": 100,
  "classification": "hot",
  "reasons": [
    {
      "code": "budget.covers_price",
      "message": "Budget covers the property price.",
      "points": 35
    },
    {
      "code": "financing.cash",
      "message": "Customer can purchase with cash.",
      "points": 25
    },
    {
      "code": "timeframe.within_1_month",
      "message": "Purchase timeframe is within one month.",
      "points": 25
    },
    {
      "code": "visit.requested",
      "message": "Customer requested a property visit.",
      "points": 15
    }
  ]
}
```

Responses always contain exactly four reasons in this order: budget, financing, timeframe, and visit. Their points must sum to the response score, and the classification must match that score.

## Qualification policy

### Budget fit — maximum 35 points

The service calculates `maximum_purchase_budget / property_price` using `Decimal` values.

| Budget ratio | Points | Reason code |
| --- | ---: | --- |
| At least 100% | 35 | `budget.covers_price` |
| At least 90%, below 100% | 25 | `budget.within_90_percent` |
| At least 75%, below 90% | 15 | `budget.within_75_percent` |
| Below 75% | 0 | `budget.below_75_percent` |

Thresholds are inclusive at 100%, 90%, and 75%.

### Financing — maximum 25 points

| Financing status | Points |
| --- | ---: |
| `cash` | 25 |
| `pre_approved` | 20 |
| `needs_financing` | 5 |
| `unknown` | 0 |

### Purchase timeframe — maximum 25 points

| Purchase timeframe | Points |
| --- | ---: |
| `within_1_month` | 25 |
| `within_3_months` | 20 |
| `within_6_months` | 10 |
| `more_than_6_months` | 0 |
| `unknown` | 0 |

### Visit interest — maximum 15 points

| Visit interest | Points |
| --- | ---: |
| `true` | 15 |
| `false` | 0 |

### Classification thresholds

| Score | Classification |
| ---: | --- |
| 0–34 | `cold` |
| 35–69 | `warm` |
| 70–100 | `hot` |

The four dimensions have a natural maximum of 100 points; scores outside the 0–100 range are rejected by the domain and response validation.

## Validation behavior

All request fields are required:

- `maximum_purchase_budget`
- `property_price`
- `financing_status`
- `purchase_timeframe`
- `visit_interest`

Additional validation rules:

- Monetary values must be finite, greater than zero, contain no more than 14 total digits, and use at most two decimal places.
- `maximum_purchase_budget` and `property_price` must represent the same currency and unit. Currency conversion is outside the current API contract.
- Extra request fields are rejected.
- `visit_interest` uses strict boolean validation; strings and integers are not accepted as substitutes for JSON `true` or `false`.
- Financing status and purchase timeframe must use one of the documented enum values.
- Empty, incomplete, malformed, or otherwise invalid requests return HTTP `422 Unprocessable Entity`.

## Local setup

Python 3.11 or newer is required because the models use `enum.StrEnum`.

```bash
git clone <repository-url>
cd ai-lead-qualification-api
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Once the server is running, open the interactive Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run the full suite from the repository root:

```bash
pytest
```

Current status: **62 tests passing**.

The suite covers all scoring branches, ratio and classification boundaries, request validation, response invariants, deterministic repeated responses, and agreement between service-level and HTTP results. No code coverage percentage is claimed because this repository does not currently publish a measured coverage report.

## Project structure

```text
ai-lead-qualification-api/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application and routes
│   ├── models.py                 # Request, response, enum, and invariant models
│   └── services/
│       ├── __init__.py
│       └── qualification.py      # Pure scoring and classification functions
├── tests/
│   ├── __init__.py
│   ├── test_health.py            # Health endpoint test
│   └── test_qualification.py     # Policy, validation, and API tests
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Technology stack

- Python 3.11+
- FastAPI
- Pydantic 2
- Python `Decimal`
- pytest
- HTTPX/FastAPI TestClient
- Uvicorn

## Why the scoring engine does not use AI

The scoring engine intentionally does not call an LLM. Scores influence business prioritization, so the same inputs should always produce the same result. Fixed rules make policy changes reviewable, boundary cases testable, and outcomes auditable.

An LLM can still be useful outside this boundary—for example, extracting financing status or purchase timeframe from a conversation. That extraction result should be validated before it reaches this service. Keeping interpretation and scoring separate prevents prompt changes or model variability from silently changing business policy.

## Roadmap

Potential next steps, none of which are implemented yet:

- Configuration-driven and versioned qualification policies
- Persistence for leads and qualification results
- Authentication and authorization
- Continuous integration
- An optional LLM-based extraction layer outside the scoring engine
- Integration with broader conversational systems

## License

This project is available under the [MIT License](LICENSE).
