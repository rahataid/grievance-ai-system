import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RevokeApiKeyResponse,
    VerifyResponse,
    CreateApiKeyResponse,
)
from shared.database.models import APIKey, App
from shared.database.session import get_db
from services.auth_service.app.api_keys import hash_api_key
from services.auth_service.app.jwt import create_access_token, decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service.app.api_keys import verify_api_key, AuthContext

bearer_scheme = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new application",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new application with a name and email.
    """
    existing_app = await db.execute(select(App).where(App.email == body.email))
    if existing_app.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application with this email already exists",
        )

    app = App(
        id=uuid.uuid4(),
        name=body.name,
        email=body.email,
        is_verified=True,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)

    return RegisterResponse(message="Email registered successfully. You can now log in to receive an access token.")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and receive a JWT token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with a registered email and receive a JWT access token.
    """
    result = await db.execute(
        select(App).where(
            App.email == body.email,
            App.is_verified.is_(True),
        )
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or unverified application",
        )

    access_token = create_access_token(subject=str(app.id), claims={"email": app.email, "app_name": app.name})
    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post(
    "/api-key",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
    responses={401: {"description": "Unauthorized"}},
)
async def create_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key for the authenticated application. Requires a valid JWT access token.
    """    
    token = credentials.credentials

    try:
        claims = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    email = claims.get("email")
    subject = claims.get("sub")
    if not email or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing required claims")

    result = await db.execute(
        select(App).where(App.email == email, App.is_verified.is_(True))
    )
    app = result.scalar_one_or_none()
    if app is None or str(app.id) != str(subject):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token for application")

    # Check if an active API key already exists for this app
    existing_key_result = await db.execute(
        select(APIKey).where(
            APIKey.app_id == str(app.id),
            APIKey.is_active.is_(True),
        )
    )
    existing_key = existing_key_result.scalar_one_or_none()

    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active API key already exists for this application. Revoke it before generating a new one.",
        )

    raw_api_key = str(uuid.uuid4())
    api_key = APIKey(
        identifier=app.name,
        api_key_hash=hash_api_key(raw_api_key),
        is_active=True,
        expires_on=None,
        created_at=datetime.now(datetime.utcnow().tzinfo),
        last_used_at=None,
        app_id=str(app.id),
        scopes=None,
        rate_limit=None,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return CreateApiKeyResponse(api_key=raw_api_key)


@router.delete(
    "/api-key",
    response_model=RevokeApiKeyResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke the active API key",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "No active key found"}},
)
async def revoke_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke the active API key for the authenticated application. Requires a valid JWT access token.
    """
    token = credentials.credentials

    try:
        claims = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    email = claims.get("email")
    subject = claims.get("sub")
    if not email or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing required claims")

    result = await db.execute(
        select(App).where(App.email == email, App.is_verified.is_(True))
    )
    app = result.scalar_one_or_none()
    if app is None or str(app.id) != str(subject):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token for application")

    existing_key_result = await db.execute(
        select(APIKey).where(
            APIKey.app_id == str(app.id),
            APIKey.is_active.is_(True),
        )
    )
    existing_key = existing_key_result.scalar_one_or_none()
    if not existing_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active API key found")

    existing_key.is_active = False
    await db.commit()
    await db.refresh(existing_key)

    return RevokeApiKeyResponse(message="API key revoked successfully")


@router.get(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify an API key",
    responses={401: {"description": "Unauthorized"}},
)
async def verify(
    auth: AuthContext = Depends(verify_api_key),
):
    """
    Verify the validity of an API key.
    """    
    return VerifyResponse(status="valid", app=auth.identifier)