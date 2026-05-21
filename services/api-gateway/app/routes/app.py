from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import AppResponse, AppUpdateRequest, MessageResponse
from services.auth_service.app.api_keys import API_KEY_HEADER
from services.crud import app as app_crud
from shared.database.models import App
from shared.database.session import get_db

router = APIRouter(prefix="/apps", tags=["Apps"])


def _serialize_app(app: App) -> AppResponse:
	return AppResponse(
		id=str(app.id),
		name=app.name,
		email=app.email,
		is_verified=app.is_verified,
	)


@router.get(
	"",
	response_model=AppResponse | list[AppResponse],
	summary="Get application details",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Application not found"}},
)
async def list_apps(
	app_id: str | None = None,
	skip: int = 0,
	limit: int = 100,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Return one application's details when `app_id` is provided, otherwise return all application details.
	"""
	if app_id:
		app = await app_crud.get_app(db, app_id)
		if app is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
		return _serialize_app(app)

	apps = await app_crud.get_all_apps(db, skip=skip, limit=limit)
	return [_serialize_app(app) for app in apps]


@router.patch(
	"/{app_id}",
	response_model=AppResponse,
	summary="Update application",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Application not found"}},
)
async def update_app(
	app_id: str,
	body: AppUpdateRequest,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Update an existing application's details.
	"""
	app = await app_crud.update_app(
		db,
		app_id,
		name=body.name,
		email=str(body.email) if body.email is not None else None,
		is_verified=body.is_verified,
	)
	if app is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
	return _serialize_app(app)


@router.delete(
	"/{app_id}",
	response_model=MessageResponse,
	summary="Delete application",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Application not found"}},
)
async def delete_app(
	app_id: str,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Delete an application by its identifier.
	"""
	deleted = await app_crud.delete_app(db, app_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
	return MessageResponse(message="Application deleted successfully")
