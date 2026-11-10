"""Phase 2 formulas. Each function is one metric and nothing else.

All inputs are pandas Series aligned on the same index (one row per hospital).
A missing input gives a missing result; nothing is imputed here.
"""

import pandas as pd


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide, returning missing where the denominator is zero or negative."""
    return numerator / denominator.where(denominator > 0)


def operating_margin(operating_revenue: pd.Series, operating_expenses: pd.Series) -> pd.Series:
    """(operating revenue - operating expenses) / operating revenue."""
    return _ratio(operating_revenue - operating_expenses, operating_revenue)


def ebida(net_income: pd.Series, interest_expense: pd.Series, depreciation: pd.Series) -> pd.Series:
    """Earnings before interest, depreciation and amortization: net income + interest + depreciation."""
    return net_income + interest_expense + depreciation


def days_cash_on_hand(
    cash: pd.Series,
    short_term_investments: pd.Series,
    total_expenses: pd.Series,
    depreciation: pd.Series,
    days_in_year: int = 365,
) -> pd.Series:
    """(cash + short-term investments) / daily cash expenses.

    Daily cash expenses = (total expenses - depreciation) / days in year.
    """
    return _ratio(cash + short_term_investments, (total_expenses - depreciation) / days_in_year)


def average_age_of_plant(accumulated_depreciation: pd.Series, depreciation: pd.Series) -> pd.Series:
    """Accumulated depreciation / annual depreciation expense, in years."""
    return _ratio(accumulated_depreciation, depreciation)


def debt_to_capitalization(long_term_debt: pd.Series, net_assets: pd.Series) -> pd.Series:
    """Long-term debt / (long-term debt + net assets). Missing if capitalization is not positive."""
    return _ratio(long_term_debt, long_term_debt + net_assets)


def existing_debt_service(interest_expense: pd.Series, current_portion_ltd: pd.Series) -> pd.Series:
    """APPROXIMATION: interest expense + current portion of long-term debt.

    True debt service is interest plus scheduled principal. The cost report has no
    principal-payment line, so the current-portion proxy stands in for it.
    """
    return interest_expense + current_portion_ltd


def payer_share(payer_days: pd.Series, total_days: pd.Series) -> pd.Series:
    """One payer's share of inpatient days (payer-mix proxy)."""
    return _ratio(payer_days, total_days)
