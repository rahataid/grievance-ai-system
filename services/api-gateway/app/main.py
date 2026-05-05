from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.audio import router as audio_router

app = FastAPI(
    title="Grievance Audio Processing API",
    description=(
        "API Gateway for the Grievance Audio Processing system. "
        "Supports API key and JWT authentication."
    ),
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(audio_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
