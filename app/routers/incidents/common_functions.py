from pydantic import TypeAdapter

from app.utils.db import expenses_db
from app.utils.get_common import (
    CommonMongoGetQueryParams,
    get_records,
)

from .models import IncidentData


def query_incidents(
    mongo_params: CommonMongoGetQueryParams,
) -> list[IncidentData]:
    """
    Query the Incidents DB by a given filter and projection
    """
    mongo_params.filter = mongo_params.filter or {}
    mongo_params.filter["removed"] = {"$exists": False}  # Only get non-deleted incidents
    results = get_records(expenses_db, "Incidents", mongo_params, True)
    incident_list_adapter = TypeAdapter(list[IncidentData])
    return incident_list_adapter.validate_python(results)


def simple_incident_query(query_filter: dict) -> list[IncidentData]:
    """
    Simple query for incidents without pagination
    """
    results = list(expenses_db.Incidents.find(query_filter, {"_id": 0}))
    incident_list_adapter = TypeAdapter(list[IncidentData])
    return incident_list_adapter.validate_python(results)


def add_incident(incident_data: IncidentData) -> None:
    """
    Add a new incident to the database
    """
    expenses_db.Incidents.insert_one(incident_data.model_dump())


def update_incident_db(query: dict, update: dict) -> int:
    """
    Update an incident in the database
    Returns the number of modified documents
    """
    result = expenses_db.Incidents.update_one(query, {"$set": update})
    return result.modified_count


def delete_incident_db(query: dict) -> int:
    """
    Mark incident as removed (soft delete)
    Returns the number of modified documents
    """
    result = expenses_db.Incidents.update_one(query, {"$set": {"removed": True}})
    return result.modified_count


def get_incident_by_id(incident_id: str, group: str) -> IncidentData | None:
    """
    Get a single incident by ID and group
    """
    result = expenses_db.Incidents.find_one(
        {"incident_id": incident_id, "group": group, "removed": {"$exists": False}},
        {"_id": 0}
    )
    if result:
        incident_adapter = TypeAdapter(IncidentData)
        return incident_adapter.validate_python(result)
    return None