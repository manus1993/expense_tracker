from io import BytesIO

import jinja2
from fastapi import APIRouter, Depends, HTTPException, Security
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


def get_receipts(request: ReceiptsRequest) -> list:
    """
    Get the receipts
    """
    return list(
        expenses_db.Movements.find(
            {
                "transaction_id": {"$gte": request.begin, "$lte": request.end},
                "group": request.group,
            }
        )
    )


def create_pdf_file(receipts: list) -> bytes:
    """
    Render the receipts in a PDF file using Jinja2
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=10)

    for i, receipt in enumerate(receipts):
        if i % 4 == 0:
            pdf.add_page()

        template = jinja2.Template(TEMPLATE)
        receipt_text = template.render(receipt)

        pdf.multi_cell(0, 6, receipt_text, border=1, align="L")
        pdf.ln(3)  # Reduce espaciado entre recibos

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
    receipts = get_receipts(request)
    if not receipts:
        raise HTTPException(status_code=404, detail="No receipts found")

    pdf_file = create_pdf_file(receipts)
    return StreamingResponse(
        BytesIO(pdf_file),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=receipts.pdf"},
    )
