"""Agent orchestration — run multiple agents in parallel."""

import asyncio
import logging
from typing import Any

from bullbeararena.agents.base import AgentVerdict, run_agent
from bullbeararena.agents.prompts import AGENT_PROMPTS
from bullbeararena.config import Config

logger = logging.getLogger(__name__)

LANGUAGE_SUFFIX = {
    "zh": "\n\nIMPORTANT: You must write your entire analysis in Chinese (中文). All bull_case, bear_case, key_insights, and summary must be in Chinese. Use Chinese financial terminology.",
    "en": "",
}


def format_financial_data(snapshot_dict: dict[str, Any]) -> str:
    """Format financial snapshot into a readable string for LLM consumption."""
    lines = []
    lines.append(f"Company: {snapshot_dict.get('company_name', 'N/A')}")
    lines.append(f"Ticker: {snapshot_dict.get('ticker', 'N/A')}")
    latest = snapshot_dict.get('latest_filing_form', '')
    latest_date = snapshot_dict.get('latest_filing_date', '')
    if latest and latest_date:
        lines.append(f"Latest Filing: {latest} filed {latest_date}")
    lines.append("")

    def _fmt(val, key=""):
        if val is None:
            return "N/A"
        suffix = ""
        if "growth" in key or "margin" in key or key == "rd_to_revenue":
            suffix = "%"
        if isinstance(val, (int, float)):
            if abs(val) >= 1e9:
                return f"${val/1e9:.2f}B{suffix}"
            elif abs(val) >= 1e6:
                return f"${val/1e6:.2f}M{suffix}"
            elif suffix:
                return f"{val:.2f}{suffix}"
            else:
                return f"{val:,.0f}"
        return str(val)

    lines.append("=== INCOME STATEMENT ===")
    for key in ["revenue", "revenue_growth", "net_income", "net_income_growth",
                 "earnings_per_share", "gross_profit", "gross_margin",
                 "operating_income", "operating_margin", "rd_expense", "rd_to_revenue"]:
        val = snapshot_dict.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {_fmt(val, key)}")

    lines.append("")
    lines.append("=== BALANCE SHEET ===")
    for key in ["total_assets", "total_liabilities", "stockholders_equity",
                 "debt_to_equity", "current_ratio", "cash_and_equivalents"]:
        val = snapshot_dict.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {_fmt(val, key)}")

    lines.append("")
    lines.append("=== CASH FLOW ===")
    for key in ["operating_cash_flow", "capital_expenditures", "free_cash_flow", "fcf_margin"]:
        val = snapshot_dict.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {_fmt(val, key)}")

    lines.append("")
    lines.append("=== KEY RATIOS ===")
    for key in ["roe", "roa", "peg_hint"]:
        val = snapshot_dict.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            suffix = "%" if key in ("roe", "roa") else ""
            lines.append(f"  {label}: {val}{suffix}")

    # Add trend data if available
    trend_signals = snapshot_dict.get("trend_signals", [])
    trend_table = snapshot_dict.get("trend_table", [])
    if trend_signals:
        lines.append("")
        lines.append("=== TREND ANALYSIS (Multi-Year) ===")
        for signal in trend_signals:
            lines.append(f"  {signal}")
    if trend_table:
        lines.append("")
        lines.append("=== HISTORICAL FINANCIAL DATA ===")
        # Header
        lines.append(f"  {'Year':<6} {'Revenue':>12} {'Net Income':>12} {'FCF':>12} {'ROE':>8} {'D/E':>6} {'GM':>6}")
        lines.append(f"  {'----':<6} {'--------':>12} {'----------':>12} {'---':>12} {'---':>8} {'---':>6} {'---':>6}")
        for row in trend_table:
            rev_str = _fmt(row.get("revenue")) if row.get("revenue") else "N/A"
            ni_str = _fmt(row.get("net_income")) if row.get("net_income") else "N/A"
            fcf_str = _fmt(row.get("free_cash_flow")) if row.get("free_cash_flow") else "N/A"
            roe_str = f"{row['roe']:.1f}%" if row.get("roe") else "N/A"
            de_str = f"{row['debt_to_equity']:.2f}" if row.get("debt_to_equity") else "N/A"
            gm_str = f"{row['gross_margin']:.1f}%" if row.get("gross_margin") else "N/A"
            lines.append(f"  {str(row['year']):<6} {rev_str:>12} {ni_str:>12} {fcf_str:>12} {roe_str:>8} {de_str:>6} {gm_str:>6}")

    return "\n".join(lines)


async def run_all_agents(
    financial_data: dict[str, Any],
    agent_ids: list[str] | None = None,
    config: Config | None = None,
    language: str = "en",
) -> list[AgentVerdict]:
    """
    Run multiple investor agents in parallel.

    Args:
        financial_data: Financial snapshot dict.
        agent_ids: List of agent IDs to run. Defaults to first 5.
        config: Application configuration.
        language: "en" or "zh" for output language.

    Returns:
        List of AgentVerdict objects.
    """
    config = config or Config()
    if agent_ids is None:
        agent_ids = list(AGENT_PROMPTS.keys())[:5]

    valid_ids = [aid for aid in agent_ids if aid in AGENT_PROMPTS]
    if not valid_ids:
        raise ValueError(f"No valid agent IDs. Available: {list(AGENT_PROMPTS.keys())}")

    formatted_data = format_financial_data(financial_data)
    lang_suffix = LANGUAGE_SUFFIX.get(language, "")

    tasks = [
        run_agent(agent_id, AGENT_PROMPTS[agent_id] + lang_suffix, formatted_data, config)
        for agent_id in valid_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    verdicts = []
    for result in results:
        if isinstance(result, AgentVerdict):
            verdicts.append(result)
        else:
            logger.error(f"Agent failed with exception: {result}")

    return verdicts
