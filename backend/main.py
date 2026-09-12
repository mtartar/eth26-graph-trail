"""FastAPI app entrypoint."""

from fastapi import FastAPI

from backend.routers import transfers

app = FastAPI(title="Graph Trail API")

app.include_router(transfers.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report service liveness."""
    return {"status": "ok"}
