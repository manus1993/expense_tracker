import os
import jinja2

from pymongo import MongoClient

ATLAS_DB = os.getenv("ATLAS_DB")
ATLAS_DB_URI = os.getenv("ATLAS_DB_URI")

expenses_client = MongoClient(ATLAS_DB_URI)
expenses_db = expenses_client[ATLAS_DB]

TEMPLATE = """
RECIBO DE PAGO DE CUOTA DE MANTENIMIENTO
{{ group }} 

Recibí de {{ user }} la cantidad de $ {{ amount }} por concepto de cuota de mantenimiento correspondiente a:

{{ concept }}

Fecha: {{ created_at }}

FOLIO: {{ transaction_id }}

Firma: __________________________




"""

def get_receipts(transaction_id: str):
    return list(expenses_db.Movements.find({"transaction_id": transaction_id}, {"_id": 0}))

def parse_receipts(transactions: list):
    amount = 0
    concept = ""
    for transaction in transactions:
        amount += transaction["amount"]
        concept += transaction["name"] + ", "
    return (
        {
            "transaction_id": transactions[0]["transaction_id"],
            "group": transactions[0]["group"],
            "user": transactions[0]["user"],
            "created_at": transactions[0]["created_at"],
            "amount": amount,
            "concept": concept
        }
    )

def render_receipts(transaction_id_list: list):
    receipts_in_text = ""
    for transaction_id in transaction_id_list:
        transactions = get_receipts(transaction_id)
        print(transactions)
        parsed_receipts = parse_receipts(transactions)
        template = jinja2.Template(TEMPLATE)
        receipts_in_text += template.render(parsed_receipts)
        receipts_in_text += "========================\n"
    return receipts_in_text

if __name__ == "__main__":
    initial = input("Enter the initial transaction_id: ")
    final = input("Enter the final transaction_id: ")

    with open("receipt.txt", "w") as f:
        f.write(render_receipts(list(range(int(initial), int(final) + 1))))