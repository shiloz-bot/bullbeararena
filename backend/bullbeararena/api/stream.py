"""SSE streaming endpoint for real-time analysis updates."""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from bullbeararena.agents.orchestrator import run_agent, format_financial_data, LANGUAGE_SUFFIX
from bullbeararena.agents.prompts import AGENT_PROMPTS
from bullbeararena.agents.base import AgentVerdict
from bullbeararena.data.metrics import compute_financials
from bullbeararena.data.sec_client import SECEdgarClient
from bullbeararena.report.generator import generate_report
from bullbeararena.config import Config
from bullbeararena import AGENT_DISPLAY

logger = logging.getLogger(__name__)
router = APIRouter()


def _sse(event: str, data: dict) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_analysis(ticker: str, language: str = "en", agent_ids: Optional[list[str]] = None):
    """Async generator yielding SSE events as analysis progresses."""
    config = Config()

    # Phase 1: Fetching data
    yield _sse("status", {
        "phase": "fetching",
        "message": f"Fetching financial data for {ticker}..." if language != "zh" else f"正在获取 {ticker} 财务数据...",
    })

    try:
        client = SECEdgarClient(config)
        financials = await client.get_financials(ticker)

        yield _sse("company", {
            "company_name": financials["company_name"],
            "ticker": financials["ticker"],
            "cik": financials["cik"],
            "latest_filings": financials["latest_filings"],
        })
    except ValueError as e:
        yield _sse("error", {"message": str(e)})
        return
    except Exception as e:
        yield _sse("error", {"message": f"Failed to fetch data: {str(e)}"})
        return

    # Phase 2: Computing metrics
    yield _sse("status", {
        "phase": "computing",
        "message": "Computing financial metrics..." if language != "zh" else "计算财务指标中...",
    })

    snapshot = compute_financials(
        facts_data=financials["facts"],
        company_name=financials["company_name"],
        ticker=financials["ticker"],
        latest_filings=financials["latest_filings"],
    )

    yield _sse("metrics", snapshot.to_dict())

    # Phase 3: Running agents IN PARALLEL, pushing results as they complete
    if agent_ids is None:
        agent_ids = list(AGENT_PROMPTS.keys())[:5]

    valid_ids = [aid for aid in agent_ids if aid in AGENT_PROMPTS]
    formatted_data = format_financial_data(snapshot.to_dict())
    lang_suffix = LANGUAGE_SUFFIX.get(language, "")

    # Notify all agents starting
    for aid in valid_ids:
        info = AGENT_DISPLAY[aid]
        yield _sse("agent_start", {
            "agent_id": aid,
            "agent_name": info["name"],
            "emoji": info["emoji"],
            "style": info["style"],
            "message": f"{info['emoji']} {info['name']} is analyzing..." if language != "zh" else f"{info['emoji']} {info['name']} 正在分析...",
        })

    # Create async tasks for all agents
    async def _run_one(agent_id: str) -> tuple[str, AgentVerdict | None]:
        try:
            verdict = await run_agent(
                agent_id,
                AGENT_PROMPTS[agent_id] + lang_suffix,
                formatted_data,
                config,
            )
            return (agent_id, verdict)
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {e}")
            return (agent_id, None)

    tasks = {aid: asyncio.create_task(_run_one(aid)) for aid in valid_ids}
    pending = set(tasks.values())
    verdicts: list[AgentVerdict] = []

    # Process results as they complete (first done = first pushed)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            agent_id, verdict = task.result()
            if verdict:
                verdicts.append(verdict)
                yield _sse("agent_complete", {
                    "agent_id": agent_id,
                    "verdict": verdict.to_dict(),
                })
            else:
                yield _sse("agent_error", {
                    "agent_id": agent_id,
                    "error": "Analysis failed",
                })

    # Phase 4: Generating report (streaming)
    yield _sse("status", {
        "phase": "report",
        "message": "Generating debate report..." if language != "zh" else "生成辩论报告中...",
    })

    filing_str = ""
    if financials["latest_filings"]:
        f = financials["latest_filings"][0]
        filing_str = f"{f['form']} filed {f['date']}"

    # Stream the roundtable summary in real-time
    from bullbeararena.report.generator import generate_report_streaming

    report_chunks = []
    async for chunk in generate_report_streaming(
        company_name=financials["company_name"],
        ticker=financials["ticker"],
        latest_filing=filing_str,
        verdicts=verdicts,
        config=config,
        language=language,
    ):
        if chunk.get("type") == "roundtable_chunk":
            report_chunks.append(chunk["text"])
            yield _sse("report_chunk", {"text": chunk["text"]})
        elif chunk.get("type") == "complete":
            report = chunk["report"]
            yield _sse("complete", report)


@router.get("/analyze/stream")
async def analyze_stream(
    ticker: str = Query(..., description="Stock ticker symbol"),
    language: str = Query("en", description="Language: en or zh"),
    agents: Optional[str] = Query(None, description="Comma-separated agent IDs"),
):
    """
    Stream analysis updates via Server-Sent Events (SSE).

    Events:
    - status: Phase updates (fetching, computing, report)
    - company: Company info found
    - metrics: Financial metrics computed
    - agent_start: Agent begins analysis
    - agent_complete: Agent finished with verdict
    - agent_error: Agent failed
    - complete: Full report ready
    - error: Something went wrong
    """
    agent_ids = agents.split(",") if agents else None

    return StreamingResponse(
        _stream_analysis(ticker.upper(), language, agent_ids),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
