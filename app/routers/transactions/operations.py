from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta
from pydantic import TypeAdapter

from .models import (
    DebtDataMonth,
    ExpenseDataMonth,
    GroupDetails,
    IncomeDataMonth,
    ParsedData,
    TransactionData,
)


def get_months(initial_date: datetime) -> list[str]:
    now = datetime.now()
    months = []

    # Start at the initial date and increment by one month on each iteration
    month = initial_date
    while month <= now:
        months.append(month.strftime("%Y-%m"))
        month += relativedelta(months=1)
    return months


def parse_data(data: list[TransactionData], group_details: GroupDetails) -> ParsedData:
    return ParsedData(
        income=parse_income_data(data, group_details),
        expense=parse_expense_data(data, group_details),
        debt=parse_debt_data(data, group_details),
    )


def parse_income_data(
    data: list[TransactionData], group_details: GroupDetails
) -> list[IncomeDataMonth]:
    result_list: list[dict[str, Any]] = []
    months = get_months(group_details.created_at)
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_income": 0.0,
                "total_contributions": 0,
                "income_source": [],
            }
        )
    for transaction in data:
        if transaction.category in [
            "MONTHLY_INCOME",
            "EXTRAORDINARY_INCOME",
        ]:
            transaction_date = transaction.created_at.strftime("%Y-%m")
            for result in result_list:
                if result["datetime"] == transaction_date:
                    result["total_income"] = (
                        float(result["total_income"]) + transaction.amount
                    )
                    income_source: list = result["income_source"]  # type: ignore
                    income_source.append(
                        {
                            "transaction_id": transaction.transaction_id,
                            "user": transaction.user,
                            "name": transaction.name,
                            "amount": transaction.amount,
                            "comments": transaction.comments,
                            "category": transaction.category,
                        }
                    )
                    result["total_contributions"] = len(income_source)
    return TypeAdapter(list[IncomeDataMonth]).validate_python(result_list)


def parse_expense_data(
    data: list[TransactionData], group_details: GroupDetails
) -> list[ExpenseDataMonth]:
    result_list: list[dict[str, Any]] = []
    months = get_months(group_details.created_at)
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_expense": 0.0,
                "total_expenses": 0,
                "expense_detail": [],
            }
        )
    for transaction in data:
        if transaction.movement_type in ["expense"]:
            transaction_date = transaction.created_at.strftime("%Y-%m")
            for result in result_list:
                if result["datetime"] == transaction_date:
                    result["total_expense"] = (
                        float(result["total_expense"]) + transaction.amount
                    )
                    expense_detail: list = result["expense_detail"]  # type: ignore
                    expense_detail.append(
                        {
                            "transaction_id": transaction.transaction_id,
                            "user": transaction.user,
                            "name": transaction.name,
                            "amount": transaction.amount,
                            "comments": transaction.comments,
                            "category": transaction.category,
                        }
                    )
                    result["total_expenses"] = len(expense_detail)
    return TypeAdapter(list[ExpenseDataMonth]).validate_python(result_list)


def parse_debt_data(
    data: list[TransactionData], group_details: GroupDetails
) -> list[DebtDataMonth]:
    result_list: list[dict[str, Any]] = []
    months = get_months(group_details.created_at)
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_debt": 0.0,
                "total_contributions_in_debt": 0,
                "debt_detail": [],
            }
        )
    for transaction in data:
        if transaction.category in ["VENCIDO"]:
            if transaction.date is not None:
                transaction_date = transaction.date.strftime("%Y-%m")
                for result in result_list:
                    if result["datetime"] == transaction_date:
                        result["total_debt"] = (
                            float(result["total_debt"]) + transaction.amount
                        )
                        debt_detail: list = result["debt_detail"]  # type: ignore
                        debt_detail.append(
                            {
                                "transaction_id": transaction.transaction_id,
                                "user": transaction.user,
                                "name": transaction.name,
                                "amount": transaction.amount,
                                "comments": transaction.comments,
                                "category": transaction.category,
                            }
                        )
                        result["total_contributions_in_debt"] = len(debt_detail)
    return TypeAdapter(list[DebtDataMonth]).validate_python(result_list)


def parse_group_details(
    group_details: GroupDetails, parsed_data: ParsedData
) -> GroupDetails:
    group_details.total_income = sum(
        [month.total_income for month in parsed_data.income]
    )

    group_details.total_expense = sum(
        [month.total_expense for month in parsed_data.expense]
    )

    group_details.total_debt = sum([month.total_debt for month in parsed_data.debt])

    group_details.total_contributions = sum(
        [month.total_contributions for month in parsed_data.income]
    )

    group_details.total_pending_receipts = sum(
        [month.total_contributions_in_debt for month in parsed_data.debt]
    )

    group_details.balance = (
        group_details.total_income
        + group_details.total_debt
        - group_details.total_expense
    )

    group_details.total_available = (
        group_details.total_income - group_details.total_expense
    )

    user_with_debt = []
    for month in parsed_data.debt:
        for debt in month.debt_detail:
            if debt.user not in user_with_debt:
                user_with_debt.append(debt.user)
    user_with_debt = sorted(user_with_debt)
    group_details.users_with_debt = user_with_debt

    # Validate the result using TypeAdapter
    group_details_adapter = TypeAdapter(GroupDetails)
    return group_details_adapter.validate_python(group_details)
