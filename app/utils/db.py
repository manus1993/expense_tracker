import os

from pymongo import MongoClient

ATLAS_DB = os.getenv("ATLAS_DB")
ATLAS_DB_URI = os.getenv("ATLAS_DB_URI")

if ATLAS_DB_URI is None or ATLAS_DB is None:
    raise ValueError("Database configuration is not set properly.")

expenses_client: MongoClient = MongoClient(ATLAS_DB_URI)
expenses_db = expenses_client[ATLAS_DB]
