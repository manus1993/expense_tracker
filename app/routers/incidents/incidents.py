from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from app.utils.get_common import CommonMongoGetQueryParams
from app.utils.logger import logger
from app.utils.token import validate_access_token, OwnerObject

from .common_functions import (
    add_incident,
    delete_incident_db,
    get_incident_by_id,
    query_incidents,
    update_incident_db,
)
from .enums import IncidentStatus
from .models import (
    CreateIncident,
    IncidentData,
    SolveIncident,
    UpdateIncident,
    UpdateIncidentStatus,
)

router = APIRouter()
security = HTTPBearer()


def validate_scope(
    group_id: str,
    access_token_details: OwnerObject = Depends(validate_access_token),
    admin: bool = False,
) -> bool:
    """
    Validate the scope - only admin users can access incidents
    """
    if group_id not in access_token_details.scope:
        raise HTTPException(status_code=403, detail="Insufficient scope")
    if admin and not access_token_details.token_type.value == "admin":
        raise HTTPException(status_code=403, detail="Admin token required")
    return True


@router.get("", response_model=list[IncidentData])
async def get_incidents(
    group_id: str,
    user_id: str | None = None,
    mongo_params: CommonMongoGetQueryParams = Depends(CommonMongoGetQueryParams),
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> list[IncidentData]:
    """
    Get incidents from the database based on group and optionally user.
    Only admin users can access this endpoint.
    """
    validate_scope(group_id, access_token_details, admin=True)
    
    # Build filter
    filter_dict = {"group": group_id}
    if user_id:
        filter_dict["submitter"] = user_id
    
    # Add filter to mongo_params
    if mongo_params.filter:
        mongo_params.filter.update(filter_dict)
    else:
        mongo_params.filter = filter_dict
    
    try:
        incidents = query_incidents(mongo_params)
        logger.info("Retrieved %d incidents for group %s", len(incidents), group_id)
        return incidents
    except Exception as e:
        logger.error("Error retrieving incidents: %s", str(e))
        raise HTTPException(status_code=500, detail="Error retrieving incidents") from e


@router.post("", response_model=IncidentData)
async def create_incident(
    payload: CreateIncident,
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> IncidentData:
    """
    Create a new incident. Only admin users can access this endpoint.
    solved_by defaults to empty string.
    """
    validate_scope(payload.group, access_token_details, admin=True)
    
    try:
        incident = IncidentData(
            incident_type=payload.incident_type,
            incident_status=payload.incident_status,
            message=payload.message,
            submitter=payload.submitter,
            group=payload.group,
            solved_by=""  # Default value
        )
        add_incident(incident)
        logger.info("Created incident %s for group %s", incident.incident_id, payload.group)
        return incident
    except Exception as e:
        logger.error("Error creating incident: %s", str(e))
        raise HTTPException(status_code=500, detail="Error creating incident") from e


@router.put("/{group_id}/{incident_id}")
async def update_incident(
    group_id: str,
    incident_id: str,
    payload: UpdateIncident,
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> dict[str, Any]:
    """
    Update an incident. incident_type, incident_status, and message can be updated.
    Only admin users can access this endpoint.
    """
    validate_scope(group_id, access_token_details, admin=True)
    
    # Check if incident exists
    existing_incident = get_incident_by_id(incident_id, group_id)
    if not existing_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Build update dictionary with only non-None values
    update_dict = {}
    if payload.incident_type is not None:
        update_dict["incident_type"] = payload.incident_type
    if payload.incident_status is not None:
        update_dict["incident_status"] = payload.incident_status
    if payload.message is not None:
        update_dict["message"] = payload.message
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    try:
        query = {"incident_id": incident_id, "group": group_id}
        modified_count = update_incident_db(query, update_dict)
        
        if modified_count == 0:
            raise HTTPException(status_code=404, detail="Incident not found or no changes made")
        
        logger.info("Updated incident %s in group %s", incident_id, group_id)
        return {"message": "Incident updated successfully", "modified_count": modified_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating incident: %s", str(e))
        raise HTTPException(status_code=500, detail="Error updating incident") from e


@router.delete("/{group_id}/{incident_id}")
async def delete_incident(
    group_id: str,
    incident_id: str,
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> dict[str, Any]:
    """
    Delete an incident (soft delete by marking as removed).
    Only admin users can access this endpoint.
    """
    validate_scope(group_id, access_token_details, admin=True)
    
    # Check if incident exists
    existing_incident = get_incident_by_id(incident_id, group_id)
    if not existing_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        query = {"incident_id": incident_id, "group": group_id}
        modified_count = delete_incident_db(query)
        
        if modified_count == 0:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        logger.info("Deleted incident %s from group %s", incident_id, group_id)
        return {"message": "Incident deleted successfully", "modified_count": modified_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting incident: %s", str(e))
        raise HTTPException(status_code=500, detail="Error deleting incident") from e


@router.patch("/{group_id}/{incident_id}/status")
async def update_incident_status(
    group_id: str,
    incident_id: str,
    payload: UpdateIncidentStatus,
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> dict[str, Any]:
    """
    Update the status of an incident.
    Only admin users can access this endpoint.
    """
    validate_scope(group_id, access_token_details, admin=True)
    
    # Check if incident exists
    existing_incident = get_incident_by_id(incident_id, group_id)
    if not existing_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        query = {"incident_id": incident_id, "group": group_id}
        update_dict = {"incident_status": payload.incident_status}
        modified_count = update_incident_db(query, update_dict)
        
        if modified_count == 0:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        logger.info("Updated incident %s status to %s in group %s", incident_id, payload.incident_status, group_id)
        return {
            "message": "Incident status updated successfully", 
            "incident_status": payload.incident_status,
            "modified_count": modified_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating incident status: %s", str(e))
        raise HTTPException(status_code=500, detail="Error updating incident status") from e


@router.patch("/{group_id}/{incident_id}/solve")
async def solve_incident(
    group_id: str,
    incident_id: str,
    payload: SolveIncident,
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> dict[str, Any]:
    """
    Mark an incident as solved by adding the solved_by user.
    Only admin users can access this endpoint.
    """
    validate_scope(group_id, access_token_details, admin=True)
    
    # Check if incident exists
    existing_incident = get_incident_by_id(incident_id, group_id)
    if not existing_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Check if already solved
    if existing_incident.solved_by:
        raise HTTPException(
            status_code=400, 
            detail=f"Incident already solved by {existing_incident.solved_by}"
        )
    
    try:
        query = {"incident_id": incident_id, "group": group_id}
        update_dict = {
            "solved_by": payload.solved_by,
            "incident_status": IncidentStatus.RESOLVED
        }
        modified_count = update_incident_db(query, update_dict)
        
        if modified_count == 0:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        logger.info("Marked incident %s as solved by %s", incident_id, payload.solved_by)
        return {
            "message": "Incident marked as solved successfully", 
            "solved_by": payload.solved_by,
            "incident_status": IncidentStatus.RESOLVED,
            "modified_count": modified_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error solving incident: %s", str(e))
        raise HTTPException(status_code=500, detail="Error solving incident") from e