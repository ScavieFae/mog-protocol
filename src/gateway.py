"""Two-tool gateway MCP server for the Mog Protocol marketplace."""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
NVM_AGENT_ID = os.getenv("NVM_GATEWAY_AGENT_ID") or os.getenv("NVM_AGENT_ID")

if not NVM_API_KEY or not NVM_AGENT_ID:
    print(
        "Waiting for Nevermined API keys. "
        "Set NVM_API_KEY and NVM_AGENT_ID (or NVM_GATEWAY_AGENT_ID) in .env"
    )
    sys.exit(0)

from payments_py import Payments, PaymentOptions
from payments_py.mcp import PaymentsMCP

from src.pricing import get_current_price
from src.services import catalog
from src.txlog import txlog

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

mcp = PaymentsMCP(
    payments,
    name="mog-gateway",
    agent_id=NVM_AGENT_ID,
    version="1.0.0",
    description="API marketplace. Two tools: find_service (free discovery) and buy_and_call (pay per use).",
)


def _gateway_credits(ctx: dict) -> int:
    """Dynamic credits for buy_and_call — surge pricing based on recent demand."""
    service_id = (ctx.get("args") or {}).get("service_id", "")
    service = catalog.get(service_id)
    if service:
        price, _ = get_current_price(service_id, service.price_credits)
        return price
    return 1


@mcp.tool(credits=0)
def find_service(query: str, budget: int = None) -> str:
    """Search the marketplace for services matching your need.

    Returns JSON array of up to 5 matches.
    Each match has: service_id, name, description, price, example_params, provider.
    Pass service_id to buy_and_call to execute the service.
    """
    matches = catalog.search(query, budget=budget, top_k=5)
    if not matches:
        txlog.log({
            "type": "unmet_demand",
            "query": query,
            "budget": budget,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "matches_returned": 0,
        })
    return json.dumps(matches)


@mcp.tool(credits=_gateway_credits)
def buy_and_call(service_id: str, params: dict) -> str:
    """Pay for and execute a service in one call. Payment is handled automatically.

    Args:
        service_id: From find_service results
        params: Parameters for the underlying service (see example_params from find_service)

    Returns JSON with result and _meta containing credits_charged and service_id.
    """
    service = catalog.get(service_id)
    if service is None:
        return json.dumps({
            "error": f"Service '{service_id}' not found. Use find_service to discover available services.",
            "_meta": {"service_id": service_id, "credits_charged": 0},
        })
    if service.handler is None:
        return json.dumps({
            "error": f"Service '{service_id}' has no handler registered.",
            "_meta": {"service_id": service_id, "credits_charged": 0},
        })
    price, surge_multiplier = get_current_price(service_id, service.price_credits)
    t0 = time.monotonic()
    try:
        result = service.handler(**(params or {}))
    except Exception as exc:
        txlog.log({
            "type": "buy_and_call",
            "service_id": service_id,
            "credits_charged": 0,
            "success": False,
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return json.dumps({
            "error": str(exc),
            "_meta": {"service_id": service_id, "credits_charged": 0},
        })
    txlog.log({
        "type": "buy_and_call",
        "service_id": service_id,
        "credits_charged": price,
        "success": True,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return json.dumps({
        "result": result,
        "_meta": {
            "credits_charged": price,
            "service_id": service_id,
            "surge_multiplier": surge_multiplier,
        },
    })


async def main():
    port = int(os.getenv("GATEWAY_PORT", "4000"))
    print(f"Starting Mog Gateway MCP server on port {port}")
    result = await mcp.start(port=port)
    stop = result.get("stop")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        if stop:
            await stop()


if __name__ == "__main__":
    asyncio.run(main())
