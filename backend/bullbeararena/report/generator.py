"""Report generation — combine agent verdicts into a final analysis."""

import json
import logging
from dataclasses import dataclass
from typing import Any

import litellm

from bullbeararena.agents.base import AgentVerdict, RATING_VALUES
from bullbeararena.config import Config

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT_EN = """You are a financial moderator hosting a roundtable debate between legendary investors.
You have analysis from multiple investors, each with their own style and perspective.

Generate a structured debate report in JSON format:
{
    "title": "Catchy title for the debate",
    "consensus": ["points where most investors agree"],
    "debates": [
        {
            "topic": "The debate topic",
            "positions": {"Agent Name": "their position"},
            "verdict": "who makes the most compelling case and why"
        }
    ],
    "overall_score": 0-100,
    "overall_sentiment": "Very Bullish | Bullish | Neutral | Bearish | Very Bearish",
    "roundtable_summary": "A 3-5 paragraph narrative written as a roundtable discussion. Use the investors' names and reference their specific points. Make it read like a lively debate. Include direct quotes from their analyses.",
    "final_recommendation": "One paragraph final takeaway"
}

Rules:
- overall_score: 0 = all Strong Sell, 50 = all Hold, 100 = all Strong Buy. Weight by confidence.
- Be entertaining but substantive
- Reference specific numbers from the analyses
- Make the roundtable read like a real conversation

Respond with ONLY valid JSON, no other text."""

REPORT_SYSTEM_PROMPT_ZH = """你是一位金融主持人，正在主持一场传奇投资者之间的圆桌辩论。
你有多位投资者的分析，每位都有自己独特的风格和视角。

请生成一份结构化的辩论报告，格式为JSON：
{
    "title": "辩论的醒目标题",
    "consensus": ["大多数投资者同意的观点"],
    "debates": [
        {
            "topic": "辩论话题",
            "positions": {"投资者姓名": "他们的立场"},
            "verdict": "谁的论点最有说服力，为什么"
        }
    ],
    "overall_score": 0-100,
    "overall_sentiment": "非常看多 | 看多 | 中性 | 看空 | 非常看空",
    "roundtable_summary": "3-5段的圆桌讨论叙事。使用投资者的名字并引用他们的具体观点。让它读起来像一场生动的辩论。包含他们分析中的直接引用。",
    "final_recommendation": "一段话的最终建议"
}

规则：
- overall_score: 0 = 全部强烈卖出, 50 = 全部持有, 100 = 全部强烈买入。按置信度加权。
- 既要有趣又要有实质内容
- 引用分析中的具体数字
- 让圆桌讨论读起来像真实的对话

只返回有效的JSON，不要有其他文字。"""


@dataclass
class ArenaReport:
    """The final arena report combining all agent analyses."""

    company_name: str
    ticker: str
    latest_filing: str
    agent_verdicts: list[AgentVerdict]
    title: str = ""
    consensus: list[str] = None
    debates: list[dict] = None
    overall_score: float = 0
    overall_sentiment: str = ""
    roundtable_summary: str = ""
    final_recommendation: str = ""

    def __post_init__(self):
        if self.consensus is None:
            self.consensus = []
        if self.debates is None:
            self.debates = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "latest_filing": self.latest_filing,
            "overall_score": self.overall_score,
            "overall_sentiment": self.overall_sentiment,
            "title": self.title,
            "consensus": self.consensus,
            "debates": self.debates,
            "agent_verdicts": [v.to_dict() for v in self.agent_verdicts],
            "roundtable_summary": self.roundtable_summary,
            "final_recommendation": self.final_recommendation,
        }


def compute_raw_score(verdicts: list[AgentVerdict]) -> float:
    """Compute a weighted average score from agent verdicts."""
    if not verdicts:
        return 50.0

    total_weight = 0.0
    weighted_sum = 0.0
    for v in verdicts:
        w = v.confidence
        weighted_sum += v.rating_value * w
        total_weight += w

    if total_weight == 0:
        return 50.0

    # Normalize to 0-100 scale (1-5 → 0-100)
    avg = weighted_sum / total_weight
    return round((avg - 1) / 4 * 100, 1)


async def generate_report(
    company_name: str,
    ticker: str,
    latest_filing: str,
    verdicts: list[AgentVerdict],
    config: Config | None = None,
    language: str = "en",
) -> ArenaReport:
    """
    Generate the final arena report from agent verdicts.
    """
    config = config or Config()

    raw_score = compute_raw_score(verdicts)

    # Determine sentiment
    if raw_score >= 80:
        sentiment = "Very Bullish 🐂🐂🐂"
    elif raw_score >= 60:
        sentiment = "Bullish 🐂🐂"
    elif raw_score >= 40:
        sentiment = "Neutral ⚖️"
    elif raw_score >= 20:
        sentiment = "Bearish 🐻🐻"
    else:
        sentiment = "Very Bearish 🐻🐻🐻"

    # Build prompt with agent analyses
    analyses_text = ""
    for v in verdicts:
        analyses_text += f"\n--- {v.emoji} {v.agent_name} ({v.style}) ---\n"
        analyses_text += f"Rating: {v.rating} (confidence: {v.confidence:.0%})\n"
        analyses_text += f"Bull case: {json.dumps(v.bull_case)}\n"
        analyses_text += f"Bear case: {json.dumps(v.bear_case)}\n"
        analyses_text += f"Key insights: {json.dumps(v.key_insights)}\n"
        analyses_text += f"Summary: {v.summary}\n"

    messages = [
        {"role": "system", "content": REPORT_SYSTEM_PROMPT_ZH if language == "zh" else REPORT_SYSTEM_PROMPT_EN},
        {"role": "user", "content": f"Company: {company_name} ({ticker})\nLatest Filing: {latest_filing}\n\nAgent Analyses:{analyses_text}"},
    ]

    try:
        kwargs = {
            "model": config.litellm_model,
            "messages": messages,
            "temperature": 0.5,
        }
        if config.llm_api_key:
            kwargs["api_key"] = config.llm_api_key
        if config.effective_base_url:
            kwargs["api_base"] = config.effective_base_url

        response = await litellm.acompletion(**kwargs)

        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        return ArenaReport(
            company_name=company_name,
            ticker=ticker,
            latest_filing=latest_filing,
            agent_verdicts=verdicts,
            title=data.get("title", f"{company_name} Arena Analysis"),
            consensus=data.get("consensus", []),
            debates=data.get("debates", []),
            overall_score=data.get("overall_score", raw_score),
            overall_sentiment=data.get("overall_sentiment", sentiment),
            roundtable_summary=data.get("roundtable_summary", ""),
            final_recommendation=data.get("final_recommendation", ""),
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}")

        # Fallback: return basic report without LLM narrative
        return ArenaReport(
            company_name=company_name,
            ticker=ticker,
            latest_filing=latest_filing,
            agent_verdicts=verdicts,
            title=f"{company_name} Arena Analysis",
            overall_score=raw_score,
            overall_sentiment=sentiment,
            roundtable_summary="Report narrative generation failed. See individual agent analyses above.",
            final_recommendation="Unable to generate final recommendation.",
        )
