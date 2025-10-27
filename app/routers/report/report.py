from io import BytesIO

import jinja2
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fpdf import FPDF

from app.routers.transactions.transactions import get_parsed_data, validate_scope
from app.utils.db import expenses_db
from app.utils.token import OwnerObject, validate_access_token

from .models import BalanceRequest, ReceiptsRequest

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

BALANCE_TEMPLATE = """
ESTADO DE CUENTA - {{ group }}
{{ year }}-{{ month }}
_________________________________________________________________________________
        Ingresos totales
            {{ group_details['total_income'] }}
        Gastos totales
            {{ group_details['total_expense'] }}
        Cuotas por cobrar
            {{ group_details['total_debt'] }}
        Balance
            {{ group_details['balance'] }}
        Ingresos correspondientes al mes en curso:
            {{ monthly_income }}
        Gastos del mes en curso:
            {{ monthly_expense }}
        _____________________________________________
        Disponible
            {{ group_details['total_available'] }}


----------- Detalles de gastos del mes ----------{% for category in categories %}
--------------- {{ category['name'] }}{% for expense in category['expenses'] %}
    Monto: {{ expense['amount'] }} \t\t - {{ expense['name'] }}{% endfor %}{% endfor %}

--------------- Deptos con adeudo:
    {{ users_with_debt }}

Atte. Administración {{ group }}
"""  # noqa: E501


def get_receipts(transaction_id: str, group: str) -> list[dict]:
    return list(
        expenses_db.Movements.find(
            {"transaction_id": transaction_id, "group": group}, {"_id": 0}
        )
    )


def parse_receipts(transactions: list) -> dict:
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


def render_receipts(transaction_id_list: list, group: str) -> list:
    receipts_in_text = []
    for transaction_id in transaction_id_list:
        transactions = get_receipts(transaction_id, group)
        parsed_receipts = parse_receipts(transactions)
        template = jinja2.Template(TEMPLATE)
        receipts_in_text.append(template.render(parsed_receipts))
    return receipts_in_text


def create_pdf_file(receipts: list) -> bytes:
    """
    Render the receipts in a PDF file with three receipts per page.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=10)
    pdf.add_page()

    receipt_per_page = 3
    count = 0

    for receipt in receipts:
        if count and count % receipt_per_page == 0:
            pdf.add_page()

        pdf.multi_cell(0, 6, receipt, border=1, align="L")
        pdf.ln(5)  # Adds some space between receipts
        count += 1

    return bytes(pdf.output(dest="S"))


def create_pdf_balance(content: str) -> bytes:
    """
    Render the balance in a PDF file.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Courier", size=8)
    pdf.add_page()

    pdf.multi_cell(0, 6, content, border=0, align="L")

    return bytes(pdf.output(dest="S"))


@router.post("/download/receipts")
async def download_receipt(
    request: ReceiptsRequest,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> StreamingResponse:
    """
    Download the receipts
    """
    validate_scope(request.group, access_token_details)
    receipts_list = render_receipts(
        list(range(int(request.start_at), int(request.end_at) + 1)),
        request.group,
    )
    pdf_file = create_pdf_file(receipts_list)
    return StreamingResponse(
        BytesIO(pdf_file),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=receipts.pdf"},
    )


def get_categories_with_expenses(expenses: list) -> list[dict]:
    category_map: dict[str, list[dict]] = {}
    for expense in expenses:
        for expense_detail in expense["expense_detail"]:
            category = expense_detail["category"]
            if category not in category_map:
                category_map[category] = []
            category_map[category].append(expense_detail)

    return [
        {"name": category, "expenses": details}
        for category, details in category_map.items()
    ]


def estimate_monthly_income(income: list) -> float:
    total = 0
    for inc in income:
        for income_detail in inc["income_source"]:
            total += income_detail["amount"]
    return total


def estimate_monthly_expense(expense: list) -> float:
    total = 0
    for exp in expense:
        for expense_detail in exp["expense_detail"]:
            total += expense_detail["amount"]
    return total


@router.post("/download/balance")
async def download_balance(
    request: BalanceRequest,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: OwnerObject = Depends(validate_access_token),
) -> StreamingResponse:
    """
    Download the receipts
    """
    validate_scope(request.group, access_token_details)
    data_per_month = {}
    try:
        data_per_month = await get_parsed_data(
            group_id=request.group,
            user_id=None,
            date=request.year + "-" + request.month,
            access_token=access_token,
            access_token_details=access_token_details,
        )
        parsed_expenses = data_per_month["parsed_data"].dict()["expense"]
        parsed_income = data_per_month["parsed_data"].dict()["income"]
    except HTTPException:
        parsed_expenses = []
        parsed_income = []

    monthly_income = estimate_monthly_income(parsed_income)
    monthly_expense = estimate_monthly_expense(parsed_expenses)
    general_data = await get_parsed_data(
        group_id=request.group,
        user_id=None,
        date=None,
        access_token=access_token,
        access_token_details=access_token_details,
    )
    user_with_debt = ""
    for user in general_data["group_details"]["users_with_debt"]:
        user_with_debt += user.replace("DEPTO", "")

    data = {
        "group": request.group,
        "group_details": general_data["group_details"],
        "users_with_debt": user_with_debt,
        "year": request.year,
        "month": request.month,
        "categories": get_categories_with_expenses(parsed_expenses),
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
    }
    template = jinja2.Template(BALANCE_TEMPLATE)
    content = template.render(data)
    pdf_file = create_pdf_balance(content)
    return StreamingResponse(
        BytesIO(pdf_file),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=receipts.pdf"},
    )
