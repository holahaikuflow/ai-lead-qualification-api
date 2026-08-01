from fastapi import FastAPI

from app.models import LeadQualificationRequest, LeadQualificationResponse
from app.services.qualification import qualify_lead

app = FastAPI(
    title="AI Lead Qualification API",
    version="0.2.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/leads/qualify",
    response_model=LeadQualificationResponse,
)
def qualify_lead_endpoint(
    lead: LeadQualificationRequest,
) -> LeadQualificationResponse:
    return qualify_lead(lead)
