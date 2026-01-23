from fastapi import FastAPI

from harmonization_framework.api.routes.health import router as health_router

app = FastAPI(title="Harmonization Framework API")

app.include_router(health_router, prefix="/health")
