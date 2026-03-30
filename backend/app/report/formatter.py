"""Markdown report formatter for BullBearArena."""

from typing import Any

from .generator import ArenaReport
from ..data.metrics import FinancialSnapshot


def _format_number(val: float | int | None) -> str:
    """Format a number for display."""
    if val is None:
        return "N/A"
    if isinstance(val, float):
        if abs(val) >= 1e9:
            return f"${val/1e9:.2f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:.2f}M"
        elif abs(val) >= 1e3:
            return f"${val/1e3:.1f}K"
        else:
            return f"${val:.2f}"
    return f"${val:,}"


def _rating_emoji(rating: str) -> str:
    """Get emoji for a rating."""
    return {
        "Strong Buy": "🟢🟢",
        "Buy": "🟢",
        "Hold": "🟡",
        "Sell": "🔴",
        "Strong Sell": "🔴🔴",
    }.get(rating, "⚪")


def _score_bar(score: float) -> str:
    """Generate a visual score bar."""
    filled = int(score / 10)
    empty = 10 - filled
    if score >= 70:
        color = "🟩"
    elif score >= 40:
        color = "🟨"
    else:
        color = "🟥"
    return f"{color * filled}{⬜ * empty} {score}/100"


def format_report_markdown(report: ArenaReport, snapshot: FinancialSnapshot) -> str:
    """Format the arena report as a Markdown string."""
    lines = []

    # Header
    lines.append(f"# 🏟️ {report.title}")
    lines.append("")
    lines.append(f"**{report.company_name}** ({report.ticker}) | {report.latest_filing}")
    lines.append("")

    # Overall Score
    lines.append("## 📊 Overall Score")
    lines.append("")
    lines.append(f"**{report.overall_score}/100** — {report.overall_sentiment}")
    lines.append("")
    lines.append(_score_bar(report.overall_score))
    lines.append("")

    # Agent Verdicts Table
    lines.append("## 🤖 Agent Verdicts")
    lines.append("")
    lines.append("| Agent | Rating | Confidence | Key Insight |")
    lines.append("|-------|--------|------------|-------------|")

    for v in report.agent_verdicts:
        insight = ""
        if v.bull_case:
            insight = v.bull_case[0]
        elif v.key_insights:
            first_key = next(iter(v.key_insights))
            insight = f"{first_key}: {v.key_insights[first_key]}"
        insight = insight[:50] + "..." if len(insight) > 50 else insight
        lines.append(
            f"| {v.emoji} **{v.agent_name}** ({v.style}) "
            f"| {_rating_emoji(v.rating)} {v.rating} "
            f"| {v.confidence:.0%} "
            f"| {insight} |"
        )
    lines.append("")

    # Individual Agent Analyses
    lines.append("## 📋 Individual Analyses")
    lines.append("")

    for v in report.agent_verdicts:
        lines.append(f"### {v.emoji} {v.agent_name} — {v.rating} ({v.confidence:.0%} confidence)")
        lines.append("")
        lines.append(f"*"{v.summary}"*")
        lines.append("")

        if v.bull_case:
            lines.append("**Bull Case:**")
            for point in v.bull_case:
                lines.append(f"- ✅ {point}")
            lines.append("")

        if v.bear_case:
            lines.append("**Bear Case:**")
            for point in v.bear_case:
                lines.append(f"- ⚠️ {point}")
            lines.append("")

        if v.key_insights:
            lines.append("**Key Insights:**")
            for metric, commentary in v.key_insights.items():
                lines.append(f"- **{metric}**: {commentary}")
            lines.append("")

    # Consensus
    if report.consensus:
        lines.append("## 🤝 Consensus")
        lines.append("")
        for point in report.consensus:
            lines.append(f"- {point}")
        lines.append("")

    # Debates
    if report.debates:
        lines.append("## ⚔️ Key Debates")
        lines.append("")
        for debate in report.debates:
            lines.append(f"### {debate.get('topic', 'Debate')}")
            lines.append("")
            positions = debate.get("positions", {})
            for agent, position in positions.items():
                lines.append(f"- **{agent}**: {position}")
            lines.append(f"\n> 💡 **Verdict**: {debate.get('verdict', 'N/A')}")
            lines.append("")

    # Roundtable Summary
    if report.roundtable_summary:
        lines.append("## 🏛️ Roundtable Discussion")
        lines.append("")
        lines.append(report.roundtable_summary)
        lines.append("")

    # Final Recommendation
    if report.final_recommendation:
        lines.append("## 🎯 Final Takeaway")
        lines.append("")
        lines.append(report.final_recommendation)
        lines.append("")

    # Financial Summary
    lines.append("## 📈 Financial Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")

    metrics = [
        ("Revenue", _format_number(snapshot.revenue)),
        ("Revenue Growth", f"{snapshot.revenue_growth}%" if snapshot.revenue_growth is not None else "N/A"),
        ("Net Income", _format_number(snapshot.net_income)),
        ("EPS", f"${snapshot.earnings_per_share:.2f}" if snapshot.earnings_per_share else "N/A"),
        ("Gross Margin", f"{snapshot.gross_margin}%" if snapshot.gross_margin is not None else "N/A"),
        ("Operating Margin", f"{snapshot.operating_margin}%" if snapshot.operating_margin is not None else "N/A"),
        ("Free Cash Flow", _format_number(snapshot.free_cash_flow)),
        ("FCF Margin", f"{snapshot.fcf_margin}%" if snapshot.fcf_margin is not None else "N/A"),
        ("ROE", f"{snapshot.roe}%" if snapshot.roe is not None else "N/A"),
        ("Debt/Equity", f"{snapshot.debt_to_equity:.2f}" if snapshot.debt_to_equity is not None else "N/A"),
        ("Current Ratio", f"{snapshot.current_ratio:.2f}" if snapshot.current_ratio is not None else "N/A"),
        ("R&D/Revenue", f"{snapshot.rd_to_revenue}%" if snapshot.rd_to_revenue is not None else "N/A"),
    ]

    for label, value in metrics:
        lines.append(f"| {label} | {value} |")
    lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append("")
    lines.append("*⚠️ **Disclaimer**: This analysis is generated by AI for educational and entertainment purposes only. "
                 "It is not financial, investment, or trading advice. Past performance does not indicate future results. "
                 "Always do your own research and consult a financial advisor before making investment decisions.*")
    lines.append("")
    lines.append("*Generated by [BullBearArena](https://github.com/YOUR_USERNAME/bullbeararena) 🐃🐻*")

    return "\n".join(lines)
