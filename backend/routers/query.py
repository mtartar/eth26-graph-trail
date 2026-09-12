"""Natural-language query endpoint: question -> filter -> matching transfers."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models import FlagResult, QueryFilter
from backend.services.data_source import get_data_source
from backend.services.nl_to_filter import question_to_filter

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """A natural-language question about stablecoin transfers."""

    question: str


class QueryResponse(BaseModel):
    """The filter the question resolved to, plus the matching transfers."""

    resolved_filter: QueryFilter
    result: FlagResult


@router.post("", response_model=QueryResponse)
def run_query(request: QueryRequest) -> QueryResponse:
    """Resolve a natural-language question into a filter, then run it."""
    query = question_to_filter(request.question)
    transfers = get_data_source().fetch_transfers(query)
    return QueryResponse(resolved_filter=query, result=FlagResult.from_transfers(transfers))
