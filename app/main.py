from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import include_api_routers

app = FastAPI(title="Issue Tracker API")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# Register routers
include_api_routers(app)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
