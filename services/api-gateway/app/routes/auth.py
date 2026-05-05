from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional

from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    VerifyResponse,
    CreateApiKeyResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new application",
)
async def register(body: RegisterRequest):
    """
    Register a new application with a name and email.
    """
    # TODO: persist app registration
    return RegisterResponse(message="registered")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and receive a JWT token",
)
async def login(body: LoginRequest):
    """
    Login with a registered email and receive a JWT access token.
    """
    # TODO: validate credentials and issue JWT
    return LoginResponse(access_token="jwt_token_here", token_type="bearer")


@router.get(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify an API key or JWT token",
    responses={401: {"description": "Unauthorized"}},
)
async def verify(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
):
    """
    Verify a provided API key (X-API-Key header) or JWT token
    (Authorization: Bearer <token> header).
    """
    if not x_api_key and not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    # TODO: validate key / token against auth-service
    return VerifyResponse(status="valid", app="my_app")


@router.post(
    "/api-key",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
    responses={401: {"description": "Unauthorized"}},
)
async def create_api_key(
    authorization: Optional[str] = Header(default=None),
):
    """
    Generate a new API key for the authenticated application.
    Requires a valid JWT token in the Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    # TODO: generate and persist API key via auth-service
    return CreateApiKeyResponse(api_key="generated_api_key")
