from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.app import router as app_router
from app.routes.auth import router as auth_router
from app.routes.audio import router as audio_router
from app.routes.category import router as category_router
from app.routes.grievance import router as grievance_router
from services.middleware.api_key_middleware import api_key_middleware    

app = FastAPI(
    title="Grievance Audio Processing API",
    description=(
        "API Gateway for the Grievance Audio Processing system. "
        "Supports API key and JWT authentication."
    ),
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}

app.middleware("http")(api_key_middleware)
app.include_router(auth_router)
app.include_router(app_router)
app.include_router(audio_router)
app.include_router(category_router)
app.include_router(grievance_router)


