from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import GrievanceResponse, GrievanceUpdateRequest, MessageResponse
from services.auth_service.app.api_keys import API_KEY_HEADER
from services.crud import grievance as grievance_crud
from shared.database.models import Grievance
from shared.database.session import get_db

router = APIRouter(prefix="/grievances", tags=["Grievances"])


def _serialize_grievance(grievance: Grievance) -> GrievanceResponse:
	return GrievanceResponse(
		id=str(grievance.id),
		audio_id=str(grievance.audio_id),
		beneficiary_id=grievance.beneficiary_id,
		confidence=grievance.confidence,
		transcript=grievance.transcript,
		language=grievance.language,
		grievance_detected=grievance.grievance_detected,
		category=grievance.category,
		sentiment=grievance.sentiment,
		urgency=grievance.urgency,
		severity_score=grievance.severity_score,
		recommended_action=grievance.recommended_action,
		keywords=grievance.keywords,
		created_at=grievance.created_at,
		updated_at=grievance.updated_at,
		api_key_id=grievance.api_key_id,
	)


@router.get(
	"",
	response_model=list[GrievanceResponse],
	summary="List grievances",
	responses={401: {"description": "Unauthorized"}, 400: {"description": "Invalid filters"}},
)
async def list_grievances(
	audio_id: str | None = None,
	beneficiary_id: str | None = None,
	skip: int = 0,
	limit: int = 100,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Return grievances filtered by `audio_id` or `beneficiary_id`, or return all grievances when no filter is provided.
	"""
	if audio_id and beneficiary_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Use either audio_id or beneficiary_id, not both",
		)

	if audio_id:
		grievances = await grievance_crud.get_grievances_by_audio(db, audio_id, skip=skip, limit=limit)
	elif beneficiary_id:
		grievances = await grievance_crud.get_grievances_by_beneficiary(
			db,
			beneficiary_id,
			skip=skip,
			limit=limit,
		)
	else:
		grievances = await grievance_crud.get_all_grievances(db, skip=skip, limit=limit)

	return [_serialize_grievance(grievance) for grievance in grievances]


@router.get(
	"/{grievance_id}",
	response_model=GrievanceResponse,
	summary="Get grievance by ID",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Grievance not found"}},
)
async def get_grievance(
	grievance_id: str,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Return a grievance record by its identifier.
	"""
	grievance = await grievance_crud.get_grievance(db, grievance_id)
	if grievance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
	return _serialize_grievance(grievance)


@router.patch(
	"/{grievance_id}",
	response_model=GrievanceResponse,
	summary="Update grievance",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Grievance not found"}},
)
async def update_grievance(
	grievance_id: str,
	body: GrievanceUpdateRequest,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Update an existing grievance record.
	"""
	grievance = await grievance_crud.update_grievance(
		db,
		grievance_id,
		transcript=body.transcript,
		language=body.language,
		confidence=body.confidence,
		grievance_detected=body.grievance_detected,
		category=body.category,
		sentiment=body.sentiment,
		urgency=body.urgency,
		severity_score=body.severity_score,
		recommended_action=body.recommended_action,
		keywords=body.keywords,
	)
	if grievance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
	return _serialize_grievance(grievance)


@router.delete(
	"/{grievance_id}",
	response_model=MessageResponse,
	summary="Delete grievance",
	responses={401: {"description": "Unauthorized"}, 404: {"description": "Grievance not found"}},
)
async def delete_grievance(
	grievance_id: str,
	_api_key: str | None = Security(API_KEY_HEADER),
	db: AsyncSession = Depends(get_db),
):
	"""
	Delete a grievance record by its identifier.
	"""
	deleted = await grievance_crud.delete_grievance(db, grievance_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
	return MessageResponse(message="Grievance deleted successfully")
