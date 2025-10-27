from datetime import datetime
from uuid import uuid4

from .enums import IncidentType, IncidentStatus

from pydantic import BaseModel, Field


class IncidentData(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_type: IncidentType
    incident_status: IncidentStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.now)
    submitter: str
    solved_by: str = ""
    group: str


class CreateIncident(BaseModel):
    incident_type: IncidentType
    incident_status: IncidentStatus = IncidentStatus.REPORTED
    message: str
    submitter: str
    group: str


class UpdateIncident(BaseModel):
    incident_type: IncidentType | None = None
    incident_status: IncidentStatus | None = None
    message: str | None = None


class UpdateIncidentStatus(BaseModel):
    incident_status: IncidentStatus


class SolveIncident(BaseModel):
    solved_by: str