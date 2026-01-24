from fastapi import FastAPI

from harmonization_framework.api.routes.health import router as health_router
from harmonization_framework.api.routes.rpc import router as rpc_router

app = FastAPI(title="Harmonization Framework API")

app.include_router(health_router, prefix="/health")
app.include_router(rpc_router, prefix="/api")
