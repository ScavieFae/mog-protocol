"""Exa Search MCP server with Nevermined payment gating."""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
NVM_AGENT_ID = os.getenv("NVM_AGENT_ID")
EXA_API_KEY = os.getenv("EXA_API_KEY")

if not NVM_API_KEY or not NVM_AGENT_ID:
    print("Waiting for Nevermined API keys. Set NVM_API_KEY and NVM_AGENT_ID in .env")
    sys.exit(0)

if not EXA_API_KEY:
    print("Missing EXA_API_KEY in .env")
    sys.exit(1)

from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP
import exa_py

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


@mcp.tool(credits=1)
def exa_search(query: str, max_results: int = 5) -> str:
    """Semantic web search. Returns relevant snippets with source URLs.
    Use when you need current information, research, or web content."""
    result = exa_client.search_and_contents(query, num_results=max_results, text=True)
    return json.dumps([
        {
            "title": r.title,
            "url": r.url,
            "snippet": (r.text or "")[:500],
        }
        for r in result.results
    ])


@mcp.tool(credits=2)
def exa_get_contents(urls: list[str]) -> str:
    """Fetch full text content from a list of URLs via Exa.
    Use when you need the complete text of specific pages found via exa_search."""
    result = exa_client.get_contents(urls, text=True)
    return json.dumps([
        {
            "url": r.url,
            "title": r.title,
            "text": r.text or "",
        }
        for r in result.results
    ])


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
