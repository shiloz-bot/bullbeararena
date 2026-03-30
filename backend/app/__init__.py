"""
BullBearArena — AI-powered stock analysis through legendary investor perspectives.
"""

LATEST_10K = "10-K"
LATEST_10Q = "10-Q"

DEFAULT_AGENTS = ["buffett", "wood", "dalio", "burry", "lynch"]

AGENT_DISPLAY = {
    "buffett": {"name": "Warren Buffett", "emoji": "🤵", "style": "Value Investing"},
    "wood": {"name": "Cathie Wood", "emoji": "👩", "style": "Disruptive Innovation"},
    "dalio": {"name": "Ray Dalio", "emoji": "🧑", "style": "Macro Cycle"},
    "burry": {"name": "Michael Burry", "emoji": "🧐", "style": "Deep Value / Contrarian"},
    "lynch": {"name": "Peter Lynch", "emoji": "👨", "style": "Pragmatic Growth"},
    "soros": {"name": "George Soros", "emoji": "🦊", "style": "Reflexivity / Macro Speculation"},
    "graham": {"name": "Ben Graham", "emoji": "🐻", "style": "Extreme Conservatism"},
    "druckenmiller": {"name": "Stanley Druckenmiller", "emoji": "🐂", "style": "Asymmetric Risk"},
}

RATINGS = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]

# SEC EDGAR requires a User-Agent header
SEC_USER_AGENT = "BullBearArena/0.1.0 (bullbeararena@example.com)"
SEC_BASE_URL = "https://data.sec.gov"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
