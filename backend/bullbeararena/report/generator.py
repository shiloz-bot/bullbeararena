"""Report generation — combine agent verdicts into a final analysis."""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import litellm

from bullbeararena.agents.base import AgentVerdict, RATING_VALUES
from bullbeararena.config import Config

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT_EN = """You are a sharp-tongued financial moderator hosting a NO-HOLDS-BARRED roundtable debate between legendary investors.

You have both initial analyses AND debate responses where investors attacked each other's arguments.

Generate a FIERY debate report in JSON format:
{
    "title": "A punchy, provocative title that captures the main conflict",
    "consensus": ["points where most investors genuinely agree — be selective, only REAL consensus"],
    "debates": [
        {
            "topic": "The most contentious debate topic",
            "positions": {"Agent Name": "their SPECIFIC position on THIS topic"},
            "clash": "The most brutal exchange — who said what to whom, with direct quotes",
            "verdict": "Who won this specific debate and WHY — be decisive"
        }
    ],
    "overall_score": 0-100,
    "overall_sentiment": "Very Bullish | Bullish | Neutral | Bearish | Very Bearish",
    "roundtable_summary": "A 3-5 paragraph DRAMATIC narrative of the debate. Include DIRECT QUOTES of investors attacking each other. Show the TENSION. Make it read like a boxing match, not a polite seminar. Who got DESTROYED? Who changed minds? Who doubled down?",
    "final_recommendation": "One hard-hitting paragraph: the most important takeaway, who was most convincing, and why"
}

CRITICAL RULES:
- overall_score: 0 = all Strong Sell, 50 = all Hold, 100 = all Strong Buy. Weight by confidence.
- Be ENTERTAINING and SUBSTANTIVE — this is financial journalism, not a research paper
- Reference SPECIFIC NUMBERS and SPECIFIC QUOTES from the debate
- Focus on DISAGREEMENTS more than agreements — conflict is interesting
- If someone got proven wrong by another investor's data point, SAY SO
- The roundtable should read like a REAL heated debate, not a summary meeting
- Maximum 5 debates — pick only the JUICIEST conflicts

Respond with ONLY valid JSON, no other text."""

REPORT_SYSTEM_PROMPT_ZH = """你是一位言辞犀利的金融主持人，正在主持一场针锋相对的圆桌辩论。

你有初始分析和辩论环节的内容，投资大师们互相攻击对方的论点。

请生成一份火药味十足的辩论报告，格式为JSON：
{
    "title": "一个尖锐、有争议性的标题，抓住核心冲突",
    "consensus": ["真正达成共识的观点 — 严格筛选，只保留真正的共识"],
    "debates": [
        {
            "topic": "最激烈的辩论话题",
            "positions": {"投资者姓名": "他们在这个话题上的具体立场"},
            "clash": "最激烈的交锋 — 谁对谁说了什么，直接引用",
            "verdict": "谁在这场辩论中赢了，为什么 — 要果断"
        }
    ],
    "overall_score": 0-100,
    "overall_sentiment": "非常看多 | 看多 | 中性 | 看空 | 非常看空",
    "roundtable_summary": "3-5段的戏剧化辩论叙事。包含投资者互相攻击的直接引用。展现紧张感。写得像拳击比赛，不是礼貌的研讨会。谁被打脸了？谁改变了观点？谁死不认错？",
    "final_recommendation": "一段话的硬核总结：最重要的结论、谁最有说服力、为什么"
}

关键规则：
- overall_score: 0 = 全部强烈卖出, 50 = 全部持有, 100 = 全部强烈买入。按置信度加权。
- 要有趣且有料 — 这是财经新闻，不是研究报告
- 引用具体的数字和辩论中的直接引用
- 重点关注分歧而不是共识 — 冲突才有趣
- 如果有人被别人的数据打脸了，直接说出来
- 圆桌讨论要像真实的激烈辩论，不是总结会议
- 最多 5 个辩论 — 只选最精彩的冲突

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
    debate_data: list[dict] | None = None,
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


async def generate_report_streaming(
    company_name: str,
    ticker: str,
    latest_filing: str,
    verdicts: list[AgentVerdict],
    config: Config | None = None,
    language: str = "en",
    debate_data: list[dict] | None = None,
):
    """
    Stream the roundtable discussion in real-time, then yield the final complete report.
    
    Yields dicts:
    - {"type": "roundtable_chunk", "text": "..."} — one token at a time
    - {"type": "complete", "report": <ArenaReport.to_dict()>} — final result
    """
    import litellm

    config = config or Config()
    raw_score = compute_raw_score(verdicts)

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

    # Build analyses text
    analyses_text = ""
    for v in verdicts:
        analyses_text += f"\n--- {v.emoji} {v.agent_name} ({v.style}) ---\n"
        analyses_text += f"Rating: {v.rating} (confidence: {v.confidence:.0%})\n"
        analyses_text += f"Bull case: {json.dumps(v.bull_case)}\n"
        analyses_text += f"Bear case: {json.dumps(v.bear_case)}\n"
        analyses_text += f"Key insights: {json.dumps(v.key_insights)}\n"
        analyses_text += f"Summary: {v.summary}\n"

    # Add debate data if available
    if debate_data:
        analyses_text += "\n\n=== DEBATE ROUND (Cross-Examination) ==="
        for d in debate_data:
            if not d:
                continue
            analyses_text += f"\n--- {d.get('emoji', '')} {d.get('agent_name', '')} responds ---"
            for c in d.get("challenges", []):
                analyses_text += f"\n🎯 Attacks {c.get('target', '')}: {c.get('counter', '')}"
            for c in d.get("concessions", []):
                analyses_text += f"\n🤝 Concedes to {c.get('source', '')}: {c.get('why', '')}"
            if d.get("final_statement"):
                analyses_text += f"\nFinal: {d['final_statement']}"

    prompt = REPORT_SYSTEM_PROMPT_ZH if language == "zh" else REPORT_SYSTEM_PROMPT_EN

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Company: {company_name} ({ticker})\nLatest Filing: {latest_filing}\n\nAgent Analyses:{analyses_text}"},
    ]

    try:
        # Step 1: First, get the structured JSON report (non-streaming)
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
        roundtable_text = data.get("roundtable_summary", "")

        # Step 2: Stream the roundtable text token by token
        # We split by characters for a typewriter effect (since we already have the full text)
        chunk_size = 3  # characters per chunk
        for i in range(0, len(roundtable_text), chunk_size):
            chunk = roundtable_text[i:i + chunk_size]
            yield {"type": "roundtable_chunk", "text": chunk}
            await asyncio.sleep(0.01)  # Small delay for typewriter effect

        # Step 3: Yield complete report
        report = ArenaReport(
            company_name=company_name,
            ticker=ticker,
            latest_filing=latest_filing,
            agent_verdicts=verdicts,
            title=data.get("title", f"{company_name} Arena Analysis"),
            consensus=data.get("consensus", []),
            debates=data.get("debates", []),
            overall_score=data.get("overall_score", raw_score),
            overall_sentiment=data.get("overall_sentiment", sentiment),
            roundtable_summary=roundtable_text,
            final_recommendation=data.get("final_recommendation", ""),
        )

        yield {"type": "complete", "report": report.to_dict()}

    except Exception as e:
        logger.error(f"Streaming report generation failed: {e}")

        report = ArenaReport(
            company_name=company_name,
            ticker=ticker,
            latest_filing=latest_filing,
            agent_verdicts=verdicts,
            title=f"{company_name} Arena Analysis",
            overall_score=raw_score,
            overall_sentiment=sentiment,
            roundtable_summary="Report generation failed.",
            final_recommendation="Unable to generate final recommendation.",
        )
        yield {"type": "complete", "report": report.to_dict()}
