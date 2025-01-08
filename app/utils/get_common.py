import json
from json import JSONDecodeError
from typing import Optional

import pymongo
from bson.json_util import loads as bson_loads
from fastapi import HTTPException, Query
from pymongo.database import Database

from .logger import logger


class CommonMongoGetQueryParams:
    def __init__(
        self,
        filter: Optional[str] = Query(
            None,
            description="JSON Mongo Filter compliant with [JSON to BSON format](https://pymongo.readthedocs.io/en/stable/api/bson/json_util.html)",  # noqa: E501
        ),
        projection: Optional[str] = Query(
            None,
            description="CSV of fields to return or a JSON projection object",
        ),
        limit: Optional[int] = Query(
            200, gt=0, le=2000, description="Number of items to return"
        ),
        skip: Optional[int] = Query(
            0, ge=0, description="Number of items to skip"
        ),
        sort_key: Optional[str] = Query(None, description="Field to sort on"),
        sort_ascending: Optional[bool] = Query(
            False, description="Sort direction"
        ),
    ):
        self.filter = self.validate_filter(filter)
        self.projection = self.validate_projection(projection)
        self.limit = limit
        self.skip = skip
        self.sort_key = sort_key
        self.sort_ascending = sort_ascending

    @staticmethod
    def validate_filter(value: Optional[str]):
        query_filter = None

        if value:
            try:
                query_filter = bson_loads(value)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="The provided filter is not valid BSON/JSON format",
                )

        return query_filter

    @staticmethod
    def validate_projection(value: Optional[str]):
        if value:
            try:
                p = json.loads(value)
                logger.debug(f"projection was JSON: {p}")
                return p
            except (JSONDecodeError, TypeError):
                logger.debug("Looks like our projection wasnt JSON")

            """
            TODO: we should do better about santizing nonsense here
            """
            logger.info(f"projection was not JSON: {value}")
            fields = {e.strip(): 1 for e in value.split(",") if e.strip()}
            if fields:
                p = {"_id": 1, **fields}
                logger.debug(f"projection was csv, here is what we got: {p}")
                return p

        return None


class CommonMongoSingleGetQueryParams:
    def __init__(
        self,
        filter: Optional[str] = Query(
            None,
            description="JSON Mongo Filter compliant with [JSON to BSON format](https://pymongo.readthedocs.io/en/stable/api/bson/json_util.html)",  # noqa: E501
        ),
        projection: Optional[str] = Query(
            None, description="CSV of fields to return"
        ),
    ):
        self.filter = self.validate_filter(filter)
        self.projection = self.validate_projection(projection)

    @staticmethod
    def validate_filter(value: Optional[str]):
        query_filter = {}

        if value:
            try:
                query_filter = bson_loads(value)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="The provided filter is not valid BSON/JSON format",
                )

        return query_filter

    @staticmethod
    def validate_projection(value: Optional[str]):
        if value:
            fields = [e.strip() for e in value.split(",") if e.strip()]
            if fields:
                return ["_id", *fields]

        return None


def get_records(
    db_instance: Database,
    collection_name: str,
    mongo_params: CommonMongoGetQueryParams,
    exclude_id: bool = True,
) -> list:
    """
    Get records from a mongo db using the common collection
    level options and removing the `_id` ObjectId from the
    records
    """
    sort_direction = (
        pymongo.ASCENDING
        if mongo_params.sort_ascending
        else pymongo.DESCENDING
    )
    sort_option = (
        [(mongo_params.sort_key, sort_direction)]
        if mongo_params.sort_key
        else None
    )
    results = []
    for entry in db_instance[collection_name].find(
        filter=mongo_params.filter,
        projection=mongo_params.projection,
        limit=mongo_params.limit,
        skip=mongo_params.skip,
        sort=sort_option,
    ):
        if entry:
            if exclude_id:
                del entry["_id"]
            results.append(entry)

    return results


def get_record(
    db_instance: Database,
    collection_name: str,
    mongo_params: CommonMongoSingleGetQueryParams,
    exclude_id: bool = True,
) -> dict:
    """
    Get a single record from a mongo db using the common collection
    level options and removing the `_id` ObjectId from the
    record
    """
    result = db_instance[collection_name].find_one(
        filter=mongo_params.filter,
        projection=mongo_params.projection,
    )
    if result and exclude_id:
        del result["_id"]

    return result
