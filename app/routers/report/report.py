from io import BytesIO

import jinja2
from fastapi import APIRouter, Depends, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fpdf import FPDF

from app.routers.transactions.transactions import validate_scope
from app.utils.db import expenses_db
from app.utils.token import validate_access_token

from .models import ReceiptsRequest

router = APIRouter()
security = HTTPBearer()

TEMPLATE = """
RECIBO DE PAGO DE CUOTA DE MANTENIMIENTO {{ group }}
FOLIO: {{ transaction_id }}

Recibí de {{ user }} la cantidad de $ {{ amount }} por concepto de cuota de mantenimiento correspondiente a: {{ concept }}

Fecha: {{ created_at }}

Atentamente,
Administración {{ group }}
"""  # noqa: E501


def get_receipts(transaction_id: str, group: str):
    return list(
        expenses_db.Movements.find(
            {"transaction_id": transaction_id, "group": group}, {"_id": 0}
        )
    )


def parse_receipts(transactions: list):
    amount = 0
    concept = ""
    for transaction in transactions:
        amount += transaction["amount"]
        concept += transaction["name"] + ", "
    return {
        "transaction_id": transactions[0]["transaction_id"],
        "group": transactions[0]["group"],
        "user": transactions[0]["user"],
        "created_at": transactions[0]["created_at"],
        "amount": amount,
        "concept": concept,
    }


def create_pdf_file(receipt: str) -> bytes:
    """
    Render the receipts in a PDF file using Jinja2
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=10)
    pdf.add_page()
    pdf.multi_cell(0, 6, receipt, border=1, align="L")
    return pdf.output(dest="S").encode("latin-1")


@router.post("/download/receipts")
async def download_file(
    request: ReceiptsRequest,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> StreamingResponse:
    """
    Download the receipts
    """
    validate_scope(request.group, access_token_details)
    transactions = get_receipts(request.transaction_id, request.group)
    parsed_receipts = parse_receipts(transactions)
    template = jinja2.Template(TEMPLATE)
    pdf_file = create_pdf_file(template.render(parsed_receipts))
    return StreamingResponse(
        BytesIO(pdf_file),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=receipts.pdf"},
    )
