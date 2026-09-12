"""Narrative summary endpoint: transfers -> short plain-English paragraph."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models import Transfer
from backend.services.narrative import summarize_transfers

router = APIRouter(prefix="/summary", tags=["summary"])


class SummaryRequest(BaseModel):
    """Transfers to summarize."""

    transfers: list[Transfer]


class SummaryResponse(BaseModel):
    """The generated narrative summary."""

    summary: str


@router.post("", response_model=SummaryResponse)
def run_summary(request: SummaryRequest) -> SummaryResponse:
    """Generate a short plain-English summary of the given transfers."""
    return SummaryResponse(summary=summarize_transfers(request.transfers))
