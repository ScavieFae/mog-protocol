"""Exa Search MCP server with Nevermined payment gating."""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
NVM_AGENT_ID = os.getenv("NVM_AGENT_ID")
EXA_API_KEY = os.getenv("EXA_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not NVM_API_KEY or not NVM_AGENT_ID:
    print("Waiting for Nevermined API keys. Set NVM_API_KEY and NVM_AGENT_ID in .env")
    sys.exit(0)

if not EXA_API_KEY:
    print("Missing EXA_API_KEY in .env")
    sys.exit(1)

if not ANTHROPIC_API_KEY:
    print("Missing ANTHROPIC_API_KEY in .env")
    sys.exit(1)

import anthropic
from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP
import exa_py

from src.catalog import ServiceCatalog
from src.txlog import txlog
from src.pricing import get_current_price

exa_client = exa_py.Exa(api_key=EXA_API_KEY)

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

mcp = PaymentsMCP(
    payments,
    name="mog-exa",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="Semantic web search via Exa. Fast, relevant results with source URLs.",
)

catalog = ServiceCatalog()
catalog.register(
    service_id="exa_search",
    name="Exa Search",
    description="Semantic web search. Returns relevant snippets with source URLs.",
    price_credits=1,
    example_params={"query": "latest AI research", "max_results": 5},
    provider="mog-exa",
)
catalog.register(
    service_id="exa_get_contents",
    name="Exa Get Contents",
    description="Fetch full text content from URLs.",
    price_credits=2,
    example_params={"urls": ["https://example.com"]},
    provider="mog-exa",
)
catalog.register(
    service_id="claude_summarize",
    name="Claude Summarize",
    description="Summarize text using Claude. Supports bullets, paragraph, or structured format.",
    price_credits=5,
    example_params={"text": "Long article text...", "format": "bullets"},
    provider="mog-exa",
)


@mcp.tool(credits=1)
def exa_search(query: str, max_results: int = 5) -> str:
    """Semantic web search. Returns relevant snippets with source URLs.
    Use when you need current information, research, or web content."""
    price, surge = get_current_price("exa_search", 1)
    t0 = time.monotonic()
    success = True
    try:
        result = exa_client.search_and_contents(query, num_results=max_results, text=True)
        data = [
            {"title": r.title, "url": r.url, "snippet": (r.text or "")[:500]}
            for r in result.results
        ]
        return json.dumps({"results": data, "_meta": {"surge_multiplier": surge, "price_charged": price}})
    except Exception:
        success = False
        raise
    finally:
        latency_ms = int((time.monotonic() - t0) * 1000)
        txlog.log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_id": "exa_search",
            "price_charged": price,
            "surge_multiplier": surge,
            "latency_ms": latency_ms,
            "success": success,
        })


@mcp.tool(credits=2)
def exa_get_contents(urls: list[str]) -> str:
    """Fetch full text content from a list of URLs via Exa.
    Use when you need the complete text of specific pages found via exa_search."""
    price, surge = get_current_price("exa_get_contents", 2)
    t0 = time.monotonic()
    success = True
    try:
        result = exa_client.get_contents(urls, text=True)
        data = [{"url": r.url, "title": r.title, "text": r.text or ""} for r in result.results]
        return json.dumps({"results": data, "_meta": {"surge_multiplier": surge, "price_charged": price}})
    except Exception:
        success = False
        raise
    finally:
        latency_ms = int((time.monotonic() - t0) * 1000)
        txlog.log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_id": "exa_get_contents",
            "price_charged": price,
            "surge_multiplier": surge,
            "latency_ms": latency_ms,
            "success": success,
        })


@mcp.tool(credits=5)
def claude_summarize(text: str, format: str = "bullets") -> str:
    """Summarize text using Claude. Supports bullets, paragraph, or structured format.
    Use when you need to condense long content into key points."""
    price, surge = get_current_price("claude_summarize", 5)
    t0 = time.monotonic()
    success = True
    try:
        format_instructions = {
            "bullets": "Summarize the following text as concise bullet points.",
            "paragraph": "Summarize the following text as a single coherent paragraph.",
            "structured": "Summarize the following text with section headers and bullet points.",
        }
        instruction = format_instructions.get(format, format_instructions["bullets"])
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"{instruction}\n\n{text}"}],
        )
        summary = message.content[0].text
        return json.dumps({"summary": summary, "_meta": {"surge_multiplier": surge, "price_charged": price}})
    except Exception:
        success = False
        raise
    finally:
        latency_ms = int((time.monotonic() - t0) * 1000)
        txlog.log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_id": "claude_summarize",
            "price_charged": price,
            "surge_multiplier": surge,
            "latency_ms": latency_ms,
            "success": success,
        })


async def main():
    port = int(os.getenv("MCP_PORT", "3000"))
    print(f"Starting Mog Exa MCP server on port {port}")
    result = await mcp.start(port=port)
    # start() returns immediately — block until interrupted
    stop = result.get("stop")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        if stop:
            await stop()


if __name__ == "__main__":
    asyncio.run(main())
