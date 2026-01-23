from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    message: str


@router.get("/")
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="The harmonization API is available")
