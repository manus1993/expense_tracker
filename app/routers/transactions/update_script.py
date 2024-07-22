
import os
import random
import time

from pymongo import MongoClient

ATLAS_DB = os.getenv("ATLAS_DB")
ATLAS_DB_URI = os.getenv("ATLAS_DB_URI")

expenses_client = MongoClient(ATLAS_DB_URI)
expenses_db = expenses_client[ATLAS_DB]

def fetch_all():
    return list(expenses_db.Movements.find({}))

def fetch_transaction(query: dict = {}):
    return list(expenses_db.Movements.find(query, {'_id': False}))

def update_transaction(id):
    expenses_db.Movements.update_one({"_id":id}, {"$set":{"user":"manus1993"}})


all_transactions = fetch_all()
for transaction in all_transactions:
    print(transaction)
    print(f"updating: {transaction['_id']}")
    update_transaction(transaction["_id"])

