"""SEC EDGAR API client for fetching financial data."""

import asyncio
from typing import Any

import httpx

from bullbeararena import SEC_BASE_URL, SEC_TICKERS_URL, SEC_USER_AGENT
from bullbeararena.config import Config


class SECEdgarClient:
    """Client for SEC EDGAR RESTful APIs."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.headers = {
            "User-Agent": self.config.sec_user_agent,
            "Accept": "application/json",
        }
        self._ticker_map: dict[str, str] | None = None

    async def _get(self, url: str) -> dict[str, Any]:
        """Make a GET request to SEC EDGAR."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def get_ticker_map(self) -> dict[str, str]:
        """Get ticker -> CIK mapping."""
        if self._ticker_map is not None:
            return self._ticker_map

        data = await self._get(SEC_TICKERS_URL)
        self._ticker_map = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", "")).zfill(10)
            if ticker and cik:
                self._ticker_map[ticker] = cik

        return self._ticker_map

    async def resolve_cik(self, ticker: str) -> str:
        """Resolve a ticker symbol to a CIK number."""
        ticker_map = await self.get_ticker_map()
        ticker = ticker.upper()
        if ticker not in ticker_map:
            raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR database")
        return ticker_map[ticker]

    async def get_company_facts(self, cik: str) -> dict[str, Any]:
        """Get all financial facts for a company."""
        url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        return await self._get(url)

    async def get_company_submissions(self, cik: str) -> dict[str, Any]:
        """Get recent filing submissions for a company."""
        url = f"{SEC_BASE_URL}/submissions/CIK{cik}.json"
        return await self._get(url)

    async def get_financials(self, ticker: str) -> dict[str, Any]:
        """
        Get structured financial data for a ticker.

        Returns a dict with:
        - company_name
        - ticker
        - cik
        - latest_filings (list of recent 10-K/10-Q dates)
        - facts (all XBRL financial data)
        """
        cik = await self.resolve_cik(ticker)
        facts_data = await self.get_company_facts(cik)
        submissions = await self.get_company_submissions(cik)

        # Extract recent 10-K / 10-Q filings
        filings_data = submissions.get("filings", {})
        recent_data = filings_data.get("recent", {}) if isinstance(filings_data, dict) else {}
        recent_forms = recent_data.get("form", [])
        recent_dates = recent_data.get("filingDate", [])
        latest_filings = []
        for form, date in zip(recent_forms, recent_dates):
            if form in ("10-K", "10-Q"):
                latest_filings.append({"form": form, "date": date})
            if len(latest_filings) >= 4:
                break

        return {
            "company_name": submissions.get("name", ""),
            "ticker": ticker.upper(),
            "cik": cik,
            "latest_filings": latest_filings,
            "facts": facts_data.get("facts", {}),
        }


def extract_metric(facts_data: dict, taxonomy: str = "us-gaap", tag: str = "") -> list[dict]:
    """
    Extract a specific metric from SEC company facts data.

    Returns a list of {value, end_date, start_date, form} sorted by date descending.
    """
    units = (
        facts_data.get("facts", {})
        .get(taxonomy, {})
        .get(tag, {})
        .get("units", {})
    )

    results = []
    for unit_key, entries in units.items():
        for entry in entries:
            val = entry.get("val")
            if val is None:
                continue
            end = entry.get("end", "")
            start = entry.get("start", "")
            form = entry.get("form", "")
            fy = entry.get("fy")
            fp = entry.get("fp")
            results.append({
                "value": val,
                "end_date": end,
                "start_date": start,
                "form": form,
                "fiscal_year": fy,
                "fiscal_period": fp,
                "unit": unit_key,
            })

    results.sort(key=lambda x: x["end_date"], reverse=True)
    return results
