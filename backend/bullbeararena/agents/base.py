"""Base agent class for BullBearArena investor agents."""

import json
import logging
from dataclasses import dataclass
from typing import Any

import litellm

from bullbeararena.config import Config

logger = logging.getLogger(__name__)

RATING_VALUES = {
    "Strong Buy": 5,
    "Buy": 4,
    "Hold": 3,
    "Sell": 2,
    "Strong Sell": 1,
}


@dataclass
class AgentVerdict:
    """Structured output from an investor agent."""

    agent_id: str
    agent_name: str
    emoji: str
    style: str
    rating: str  # Strong Buy / Buy / Hold / Sell / Strong Sell
    confidence: float  # 0.0 - 1.0
    bull_case: list[str]
    bear_case: list[str]
    key_insights: dict[str, str]
    summary: str

    @property
    def rating_value(self) -> int:
        return RATING_VALUES.get(self.rating, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "emoji": self.emoji,
            "style": self.style,
            "rating": self.rating,
            "confidence": self.confidence,
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_insights": self.key_insights,
            "summary": self.summary,
        }


OUTPUT_SCHEMA = """You MUST respond with ONLY valid JSON in this exact format, no other text:
{
    "rating": "Strong Buy | Buy | Hold | Sell | Strong Sell",
    "confidence": 0.0,
    "bull_case": ["reason1", "reason2", "reason3"],
    "bear_case": ["risk1", "risk2"],
    "key_insights": {"metric_or_theme": "your commentary"},
    "summary": "One sentence verdict"
}"""


async def run_agent(
    agent_id: str,
    system_prompt: str,
    financial_data: str,
    config: Config | None = None,
) -> AgentVerdict:
    """
    Run a single investor agent with the given financial data.

    Args:
        agent_id: Agent identifier (e.g., "buffett").
        system_prompt: The agent's system prompt.
        financial_data: Formatted financial data string.
        config: Application configuration.

    Returns:
        AgentVerdict with structured analysis.
    """
    from bullbeararena import AGENT_DISPLAY

    config = config or Config()
    info = AGENT_DISPLAY[agent_id]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this company's financial data:\n\n{financial_data}"},
    ]

    try:
        # Build kwargs for litellm
        kwargs = {
            "model": config.litellm_model,
            "messages": messages,
            "temperature": 0.3,
        }
        if config.llm_api_key:
            kwargs["api_key"] = config.llm_api_key
        if config.effective_base_url:
            kwargs["api_base"] = config.effective_base_url

        response = await litellm.acompletion(**kwargs)

        content = response.choices[0].message.content.strip()

        # Try to parse JSON from the response
        # Handle cases where LLM wraps in ```json ... ```
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        return AgentVerdict(
            agent_id=agent_id,
            agent_name=info["name"],
            emoji=info["emoji"],
            style=info["style"],
            rating=data.get("rating", "Hold"),
            confidence=float(data.get("confidence", 0.5)),
            bull_case=data.get("bull_case", []),
            bear_case=data.get("bear_case", []),
            key_insights=data.get("key_insights", {}),
            summary=data.get("summary", "No summary provided."),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Agent {agent_id} returned invalid JSON: {e}")
        return AgentVerdict(
            agent_id=agent_id,
            agent_name=info["name"],
            emoji=info["emoji"],
            style=info["style"],
            rating="Hold",
            confidence=0.0,
            bull_case=[],
            bear_case=["Analysis failed - could not parse response"],
            key_insights={},
            summary="Analysis unavailable due to parsing error.",
        )
    except Exception as e:
        logger.error(f"Agent {agent_id} failed: {e}")
        return AgentVerdict(
            agent_id=agent_id,
            agent_name=info["name"],
            emoji=info["emoji"],
            style=info["style"],
            rating="Hold",
            confidence=0.0,
            bull_case=[],
            bear_case=[f"Agent error: {str(e)[:100]}"],
            key_insights={},
            summary="Analysis unavailable.",
        )
