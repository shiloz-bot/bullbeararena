"""Configuration management for BullBearArena."""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # LLM settings
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str | None = field(default_factory=lambda: os.getenv("LLM_BASE_URL"))

    # SEC EDGAR
    sec_user_agent: str = "BullBearArena/0.1.0 (bullbeararena@example.com)"

    # App settings
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    max_concurrent_agents: int = 5

    @property
    def litellm_model(self) -> str:
        """Return the model string in litellm format."""
        if self.llm_provider == "zai":
            # Zhipu AI / GLM — use OpenAI-compatible endpoint
            return f"openai/{self.llm_model}"
        if self.llm_base_url:
            return f"openai/{self.llm_model}"
        return self.llm_model

    @property
    def effective_base_url(self) -> str | None:
        """Return the effective base URL, with provider-specific defaults."""
        if self.llm_base_url:
            return self.llm_base_url
        if self.llm_provider == "zai":
            return "https://open.bigmodel.cn/api/paas/v4"
        return None


def get_config() -> Config:
    """Get the application configuration."""
    return Config()
