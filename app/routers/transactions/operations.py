from datetime import datetime

from dateutil.relativedelta import relativedelta

from .models import (
    DebtDataMonth,
    ExpenseDataMonth,
    IncomeDataMonth,
    ParsedData,
    TransactionData,
)


def get_months(initial_date):
    # Ensure initial_date is a datetime object
    if type(initial_date) is str:
        initial_date = datetime.strptime(initial_date, "%Y-%m-%d")

    # Get the current date
    now = datetime.now()

    # Initialize the list of months
    months = []

    # Start at the initial date and increment by one month on each iteration
    month = initial_date
    while month <= now:
        # Append the month to the list
        months.append(month.strftime("%Y-%m"))

        # Increment the month
        month += relativedelta(months=1)

    return months


def parse_data(data: list[TransactionData], group_details: dict) -> ParsedData:
    return ParsedData(
        income=parse_income_data(data, group_details),
        expense=parse_expense_data(data, group_details),
        debt=parse_debt_data(data, group_details),
    )


def parse_income_data(
    data: list[TransactionData], group_details
) -> list[IncomeDataMonth]:
    result_list = []
    months = get_months(group_details["created_at"])
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_income": 0,
                "total_contributions": 0,
                "income_source": [],
            }
        )
    for transaction in data:
        if transaction["category"] in [
            "MONTHLY_INCOME",
            "EXTRAORDINARY_INCOME",
        ]:
            transaction_date = transaction["created_at"].strftime("%Y-%m")
            for result in result_list:
                if result["datetime"] == transaction_date:
                    result["total_income"] += transaction["amount"]
                    result["income_source"].append(
                        {
                            "transaction_id": transaction["transaction_id"],
                            "user": transaction["user"],
                            "name": transaction["name"],
                            "amount": transaction["amount"],
                            "comments": transaction.get("comments", None),
                            "category": transaction.get("category", None),
                        }
                    )
                    result["total_contributions"] = len(result["income_source"])
    return result_list


def parse_expense_data(
    data: list[TransactionData], group_details: dict
) -> list[ExpenseDataMonth]:
    result_list = []
    months = get_months(group_details["created_at"])
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_expense": 0,
                "total_expenses": 0,
                "expense_detail": [],
            }
        )
    for transaction in data:
        if transaction["movement_type"] in ["expense"]:
            transaction_date = transaction["created_at"].strftime("%Y-%m")
            for result in result_list:
                if result["datetime"] == transaction_date:
                    result["total_expense"] += transaction["amount"]
                    result["expense_detail"].append(
                        {
                            "transaction_id": transaction["transaction_id"],
                            "user": transaction["user"],
                            "name": transaction["name"],
                            "amount": transaction["amount"],
                            "comments": transaction.get("comments", None),
                            "category": transaction.get("category", None),
                        }
                    )
                    result["total_expenses"] = len(result["expense_detail"])
    return result_list


def parse_debt_data(
    data: list[TransactionData], group_details: dict
) -> list[DebtDataMonth]:
    result_list = []
    months = get_months(group_details["created_at"])
    for month in months:
        result_list.append(
            {
                "datetime": month,
                "total_debt": 0,
                "total_contributions_in_debt": 0,
                "debt_detail": [],
            }
        )
    for transaction in data:
        if transaction["category"] in ["VENCIDO"]:
            transaction_date = transaction["date"].strftime("%Y-%m")
            for result in result_list:
                if result["datetime"] == transaction_date:
                    result["total_debt"] += transaction["amount"]

                    result["debt_detail"].append(
                        {
                            "transaction_id": transaction["transaction_id"],
                            "user": transaction["user"],
                            "name": transaction["name"],
                            "amount": transaction["amount"],
                            "comments": transaction.get("comments", None),
                            "category": transaction.get("category", None),
                        }
                    )
                    result["total_contributions_in_debt"] = len(result["debt_detail"])
    return result_list


def parse_group_details(group_details: dict, parsed_data: ParsedData) -> dict:
    group_details["total_income"] = sum(
        [month.total_income for month in parsed_data.income]
    )

    group_details["total_expense"] = sum(
        [month.total_expense for month in parsed_data.expense]
    )

    group_details["total_debt"] = sum([month.total_debt for month in parsed_data.debt])

    group_details["total_contributions"] = sum(
        [month.total_contributions for month in parsed_data.income]
    )

    group_details["total_pending_receipts"] = sum(
        [month.total_contributions_in_debt for month in parsed_data.debt]
    )

    group_details["balance"] = (
        group_details["total_income"]
        + group_details["total_debt"]
        - group_details["total_expense"]
    )

    group_details["total_available"] = (
        group_details["total_income"] - group_details["total_expense"]
    )

    user_with_debt = []
    for month in parsed_data.debt:
        for debt in month.debt_detail:
            if debt.user not in user_with_debt:
                user_with_debt.append(debt.user)
    user_with_debt = sorted(user_with_debt)
    group_details["users_with_debt"] = user_with_debt

    return group_details
