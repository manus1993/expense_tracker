import os

from pymongo import MongoClient

ATLAS_DB = os.getenv("ATLAS_DB")
ATLAS_DB_URI = os.getenv("ATLAS_DB_URI")

expenses_client = MongoClient(ATLAS_DB_URI)
expenses_db = expenses_client[ATLAS_DB]

