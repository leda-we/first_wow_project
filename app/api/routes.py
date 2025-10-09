from fastapi import FastAPI, APIRouter


def include_api_routers(app: FastAPI) -> None:
    api_router = APIRouter(prefix="/api")

    @api_router.get("/")
    async def root() -> dict:
        return {"message": "Issue Tracker API"}

    app.include_router(api_router)
