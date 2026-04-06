"""Financial metrics calculation from SEC XBRL data."""

from dataclasses import dataclass
from typing import Any

from bullbeararena.data.sec_client import extract_metric


@dataclass
class FinancialSnapshot:
    """A snapshot of key financial metrics for a company."""

    # Company info
    company_name: str = ""
    ticker: str = ""
    latest_filing_form: str = ""
    latest_filing_date: str = ""

    # Income Statement
    revenue: float | None = None
    revenue_growth: float | None = None  # YoY %
    net_income: float | None = None
    net_income_growth: float | None = None
    earnings_per_share: float | None = None
    gross_profit: float | None = None
    gross_margin: float | None = None
    operating_income: float | None = None
    operating_margin: float | None = None
    rd_expense: float | None = None
    rd_to_revenue: float | None = None  # %

    # Balance Sheet
    total_assets: float | None = None
    total_liabilities: float | None = None
    stockholders_equity: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    cash_and_equivalents: float | None = None

    # Cash Flow
    operating_cash_flow: float | None = None
    capital_expenditures: float | None = None
    free_cash_flow: float | None = None
    fcf_margin: float | None = None  # FCF / Revenue

    # Derived Metrics
    roe: float | None = None  # Net Income / Equity
    roa: float | None = None  # Net Income / Total Assets
    peg_hint: str | None = None  # "Low" / "Medium" / "High" based on growth

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def _safe_divide(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return round(a / b, 4)


def _safe_pct(a: float | None, b: float | None) -> float | None:
    result = _safe_divide(a, b)
    if result is not None:
        return round(result * 100, 2)
    return None


def compute_financials(facts_data: dict, company_name: str = "", ticker: str = "", latest_filings: list = None) -> FinancialSnapshot:
    """
    Compute key financial metrics from SEC XBRL facts data.

    Args:
        facts_data: The 'facts' dict from SEC company facts API.
        company_name: Company name.
        ticker: Ticker symbol.
        latest_filings: List of recent filings.

    Returns:
        FinancialSnapshot with computed metrics.
    """
    snap = FinancialSnapshot(company_name=company_name, ticker=ticker)

    if latest_filings:
        snap.latest_filing_form = latest_filings[0].get("form", "")
        snap.latest_filing_date = latest_filings[0].get("date", "")

    def _filter_annual(data):
        """Filter to one value per fiscal year — the largest total per end_date group."""
        from collections import defaultdict
        
        # Group by (fiscal_year, end_date) and take the max value per group
        by_period = defaultdict(list)
        for d in data:
            key = (d.get("fiscal_year"), d.get("end_date"))
            by_period[key].append(d)
        
        # Then group by fiscal_year, take the entry with the largest absolute value
        by_year = defaultdict(list)
        for (fy, end), entries in by_period.items():
            if fy is None:
                continue
            best = max(entries, key=lambda x: abs(x["value"]))
            by_year[fy].append(best)
        
        # For each year, take the entry with the longest duration (annual total)
        result = []
        for fy in sorted(by_year.keys(), reverse=True):
            entries = by_year[fy]
            # The annual total has the earliest start_date or the largest value
            best = max(entries, key=lambda x: abs(x["value"]))
            result.append(best)
        return result

    def _yoy_growth(current_list):
        """Compute YoY growth from a list of annual data points."""
        if len(current_list) >= 2:
            current = current_list[0]["value"]
            previous = current_list[1]["value"]
            if previous != 0:
                return round((current - previous) / abs(previous) * 100, 2)
        return None

    # --- Revenue ---
    rev_data = extract_metric({"facts": facts_data}, tag="Revenues")
    if not rev_data:
        rev_data = extract_metric({"facts": facts_data}, tag="SalesRevenueNet")
    if not rev_data:
        rev_data = extract_metric({"facts": facts_data}, tag="RevenueFromContractWithCustomerExcludingAssessedTax")

    rev_annual = _filter_annual(rev_data) if rev_data else []
    if rev_annual:
        snap.revenue = rev_annual[0]["value"]
        snap.revenue_growth = _yoy_growth(rev_annual)

    # --- Net Income ---
    ni_data = extract_metric({"facts": facts_data}, tag="NetIncomeLoss")
    ni_annual = _filter_annual(ni_data) if ni_data else []
    if ni_annual:
        snap.net_income = ni_annual[0]["value"]
        snap.net_income_growth = _yoy_growth(ni_annual)

    # --- EPS ---
    eps_data = extract_metric({"facts": facts_data}, tag="EarningsPerShareBasic")
    if eps_data:
        snap.earnings_per_share = eps_data[0]["value"]

    # --- Gross Profit / Margin ---
    gp_data = extract_metric({"facts": facts_data}, tag="GrossProfit")
    if gp_data:
        snap.gross_profit = gp_data[0]["value"]
        snap.gross_margin = _safe_pct(snap.gross_profit, snap.revenue)

    # --- Operating Income / Margin ---
    oi_data = extract_metric({"facts": facts_data}, tag="OperatingIncomeLoss")
    if oi_data:
        snap.operating_income = oi_data[0]["value"]
        snap.operating_margin = _safe_pct(snap.operating_income, snap.revenue)

    # --- R&D ---
    rd_data = extract_metric({"facts": facts_data}, tag="ResearchAndDevelopmentExpense")
    if rd_data:
        snap.rd_expense = rd_data[0]["value"]
        snap.rd_to_revenue = _safe_pct(snap.rd_expense, snap.revenue)

    # --- Balance Sheet ---
    ta_data = extract_metric({"facts": facts_data}, tag="Assets")
    if ta_data:
        snap.total_assets = ta_data[0]["value"]

    tl_data = extract_metric({"facts": facts_data}, tag="Liabilities")
    if tl_data:
        snap.total_liabilities = tl_data[0]["value"]

    se_data = extract_metric({"facts": facts_data}, tag="StockholdersEquity")
    if se_data:
        snap.stockholders_equity = se_data[0]["value"]

    snap.debt_to_equity = _safe_divide(snap.total_liabilities, snap.stockholders_equity)

    # Current ratio
    ca_data = extract_metric({"facts": facts_data}, tag="AssetsCurrent")
    cl_data = extract_metric({"facts": facts_data}, tag="LiabilitiesCurrent")
    current_assets = ca_data[0]["value"] if ca_data else None
    current_liab = cl_data[0]["value"] if cl_data else None
    snap.current_ratio = _safe_divide(current_assets, current_liab)

    # Cash
    cash_data = extract_metric({"facts": facts_data}, tag="CashAndCashEquivalentsAtCarryingValue")
    if not cash_data:
        cash_data = extract_metric({"facts": facts_data}, tag="CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents")
    if cash_data:
        snap.cash_and_equivalents = cash_data[0]["value"]

    # --- Cash Flow ---
    ocf_data = extract_metric({"facts": facts_data}, tag="NetCashProvidedByUsedInOperatingActivities")
    if not ocf_data:
        ocf_data = extract_metric({"facts": facts_data}, tag="CashFlowFromOperatingActivitiesContinuingOperations")
    if ocf_data:
        snap.operating_cash_flow = ocf_data[0]["value"]

    capex_data = extract_metric({"facts": facts_data}, tag="PaymentsToAcquirePropertyPlantAndEquipment")
    if not capex_data:
        capex_data = extract_metric({"facts": facts_data}, tag="CapitalExpenditures")
    if capex_data:
        snap.capital_expenditures = abs(capex_data[0]["value"])

    if snap.operating_cash_flow is not None and snap.capital_expenditures is not None:
        snap.free_cash_flow = snap.operating_cash_flow - snap.capital_expenditures
        snap.fcf_margin = _safe_pct(snap.free_cash_flow, snap.revenue)

    # --- Derived Metrics ---
    snap.roe = _safe_pct(snap.net_income, snap.stockholders_equity)
    snap.roa = _safe_pct(snap.net_income, snap.total_assets)

    # PEG hint
    if snap.revenue_growth is not None:
        if snap.revenue_growth > 20:
            snap.peg_hint = "Low (fast growth)"
        elif snap.revenue_growth > 5:
            snap.peg_hint = "Medium (moderate growth)"
        else:
            snap.peg_hint = "High (slow/no growth)"

    return snap
