"""API routes for BullBearArena."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from bullbeararena.agents.orchestrator import run_all_agents
from bullbeararena.data.metrics import compute_financials
from bullbeararena.data.sec_client import SECEdgarClient
from bullbeararena.report.generator import generate_report
from bullbeararena.config import Config

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for stock analysis."""
    ticker: str
    agents: Optional[list[str]] = None  # Defaults to all 5
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    language: Optional[str] = "en"  # "en" or "zh"


class AnalyzeResponse(BaseModel):
    """Response body for stock analysis."""
    success: bool
    ticker: str
    company_name: str
    latest_filing: str
    overall_score: float
    overall_sentiment: str
    title: str
    consensus: list[str]
    debates: list[dict]
    agent_verdicts: list[dict]
    roundtable_summary: str
    final_recommendation: str
    disclaimer: str = "This is for educational purposes only. Not financial advice. Do your own research."


class TickerSearchResponse(BaseModel):
    """Response for ticker search."""
    ticker: str
    cik: str
    company_name: str


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "BullBearArena"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest):
    """
    Analyze a stock through multiple legendary investor perspectives.

    This endpoint:
    1. Fetches financial data from SEC EDGAR
    2. Computes key financial metrics
    3. Runs 5 investor agents in parallel
    4. Generates a debate-style report
    """
    # Build config
    config = Config()
    if request.llm_provider:
        config.llm_provider = request.llm_provider
    if request.llm_model:
        config.llm_model = request.llm_model

    try:
        # Step 1: Fetch SEC data
        client = SECEdgarClient(config)
        financials = await client.get_financials(request.ticker)

        # Step 2: Compute metrics
        snapshot = compute_financials(
            facts_data=financials["facts"],
            company_name=financials["company_name"],
            ticker=financials["ticker"],
            latest_filings=financials["latest_filings"],
        )

        # Step 3: Run investor agents
        verdicts = await run_all_agents(
            financial_data=snapshot.to_dict(),
            agent_ids=request.agents,
            config=config,
            language=request.language or "en",
        )

        if not verdicts:
            raise HTTPException(status_code=500, detail="All agents failed to produce analysis")

        # Step 4: Generate report
        latest_filing_str = ""
        if financials["latest_filings"]:
            f = financials["latest_filings"][0]
            latest_filing_str = f"{f['form']} filed {f['date']}"

        report = await generate_report(
            company_name=financials["company_name"],
            ticker=financials["ticker"],
            latest_filing=latest_filing_str,
            verdicts=verdicts,
            config=config,
            language=request.language or "en",
        )

        return AnalyzeResponse(
            success=True,
            ticker=financials["ticker"],
            company_name=financials["company_name"],
            latest_filing=latest_filing_str,
            overall_score=report.overall_score,
            overall_sentiment=report.overall_sentiment,
            title=report.title,
            consensus=report.consensus,
            debates=report.debates,
            agent_verdicts=[v.to_dict() for v in report.agent_verdicts],
            roundtable_summary=report.roundtable_summary,
            final_recommendation=report.final_recommendation,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/agents")
async def list_agents():
    """List all available investor agents."""
    from bullbeararena import AGENT_DISPLAY
    return {"agents": AGENT_DISPLAY}


@router.get("/ticker/{ticker}", response_model=TickerSearchResponse)
async def lookup_ticker(ticker: str):
    """Resolve a ticker symbol to company info."""
    config = Config()
    client = SECEdgarClient(config)
    try:
        cik = await client.resolve_cik(ticker)
        financials = await client.get_company_submissions(cik)
        return TickerSearchResponse(
            ticker=ticker.upper(),
            cik=cik,
            company_name=financials.get("name", ""),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
