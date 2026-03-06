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

from src.helicone import log_tool_call
from src.portfolio import PortfolioManager
from src.pricing import get_current_price
from src.services import catalog
from src.telemetry import telemetry, TelemetryEvent

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

portfolio = PortfolioManager()


def _gateway_credits(ctx: dict) -> int:
    """Dynamic credits for buy_and_call — look up service price with surge pricing."""
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
    telemetry.emit(TelemetryEvent(
        "find_service" if matches else "unmet_demand",
        query=query,
        budget=budget,
        matches_returned=len(matches),
        success=bool(matches),
        agent_id=NVM_AGENT_ID,
    ))
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
        telemetry.emit(TelemetryEvent(
            "buy_and_call",
            service_id=service_id, params=params,
            error=f"Service '{service_id}' not found", success=False,
            agent_id=NVM_AGENT_ID,
        ))
        raise ValueError(f"Service '{service_id}' not found. Use find_service to discover available services.")
    if service.handler is None:
        raise ValueError(f"Service '{service_id}' has no handler registered.")
    price, surge_multiplier = get_current_price(service_id, service.price_credits)
    volume = telemetry.count_calls(service_id)
    t0 = time.monotonic()
    try:
        result = service.handler(**(params or {}))
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        telemetry.emit(TelemetryEvent(
            "buy_and_call",
            service_id=service_id, service_name=service.name,
            params=params, error=str(exc), success=False,
            credits_charged=0, base_price=service.price_credits,
            surge_multiplier=surge_multiplier, volume_in_window=volume,
            latency_ms=latency_ms, agent_id=NVM_AGENT_ID,
            plan_id=os.getenv("NVM_GATEWAY_PLAN_ID", ""),
        ))
        log_tool_call(
            agent_id=NVM_AGENT_ID, plan_id=os.getenv("NVM_GATEWAY_PLAN_ID", ""),
            service_id=service_id, service_name=service.name,
            params=params, result=str(exc), credits_charged=0,
            latency_ms=latency_ms, success=False, surge_multiplier=surge_multiplier,
        )
        # Re-raise so the paywall skips credit redemption.
        # The MCP layer converts this into an error response for the buyer.
        raise
    latency_ms = int((time.monotonic() - t0) * 1000)
    telemetry.emit(TelemetryEvent(
        "buy_and_call",
        service_id=service_id, service_name=service.name,
        params=params, result=result, success=True,
        credits_charged=price, base_price=service.price_credits,
        surge_multiplier=surge_multiplier, volume_in_window=volume,
        latency_ms=latency_ms, agent_id=NVM_AGENT_ID,
        plan_id=os.getenv("NVM_GATEWAY_PLAN_ID", ""),
    ))
    portfolio.record_sale(service_id, price)
    log_tool_call(
        agent_id=NVM_AGENT_ID, plan_id=os.getenv("NVM_GATEWAY_PLAN_ID", ""),
        service_id=service_id, service_name=service.name,
        params=params, result=result, credits_charged=price,
        latency_ms=latency_ms, success=True, surge_multiplier=surge_multiplier,
    )
    return json.dumps({
        "result": result,
        "_meta": {
            "credits_charged": price,
            "service_id": service_id,
            "surge_multiplier": surge_multiplier,
        },
    })


class _BuyerCompat:
    """ASGI wrapper: translates payment-signature → Bearer, defaults Accept header."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = list(scope.get("headers", []))
            header_names = {k for k, v in headers}

            if b"accept" not in header_names:
                headers.append((b"accept", b"application/json"))

            if b"payment-signature" in header_names and b"authorization" not in header_names:
                sig_value = None
                new_headers = []
                for k, v in headers:
                    if k == b"payment-signature":
                        sig_value = v
                    else:
                        new_headers.append((k, v))
                if sig_value:
                    new_headers.append((b"authorization", b"Bearer " + sig_value))
                    headers = new_headers

            scope = {**scope, "headers": headers}

        await self.app(scope, receive, send)


async def main():
    port = int(os.getenv("PORT", os.getenv("GATEWAY_PORT", "4000")))
    print(f"Starting Mog Gateway MCP server on port {port}")

    # Patch the manager's start to wrap the FastAPI app BEFORE uvicorn launches.
    _original_start = mcp._manager.start

    async def _patched_start(config):
        result = await _original_start(config)
        return result

    # Instead of patching start (which is complex), we patch uvicorn.Config
    # to intercept the app before the server binds to it.
    import uvicorn as _uvicorn
    _OrigConfig = _uvicorn.Config

    class _WrappedConfig(_OrigConfig):
        def __init__(self, app=None, **kwargs):
            wrapped = _BuyerCompat(app) if app is not None else app
            super().__init__(app=wrapped, **kwargs)

    _uvicorn.Config = _WrappedConfig
    try:
        result = await mcp.start(port=port)
    finally:
        _uvicorn.Config = _OrigConfig
    print("Buyer compat layer active (Accept default + payment-signature → Bearer)")

    # Replace the default /health with our richer marketplace health endpoint.
    if app is not None:
        from fastapi.responses import JSONResponse as _JSONResponse

        # Remove the existing /health route registered by the oauth_router.
        app.router.routes = [
            r for r in app.router.routes if getattr(r, "path", None) != "/health"
        ]

        async def _health():
            services = catalog.services
            stats = telemetry.get_stats()
            recent = telemetry.get_recent(10, event_type="buy_and_call")
            demand = telemetry.get_recent(10, event_type="unmet_demand")
            health = {
                "status": "ok",
                "services_count": len(services),
                "services": [
                    {"service_id": s.service_id, "name": s.name, "price_credits": s.price_credits}
                    for s in services
                ],
                "stats": stats,
                "recent_transactions": recent,
                "demand_signals": demand,
                "portfolio": portfolio.get_summary(),
            }
            try:
                from src.toolkit import blockers
                recent_blockers = blockers.get_recent(5)
                health["traces"] = {
                    "recent_blockers": [
                        {"service_id": b.get("service_id"), "type": b.get("blocker_type"),
                         "recommendation": b.get("recommendation"),
                         "steps": (b.get("trace", {}).get("steps", []))}
                        for b in recent_blockers
                    ]
                }
            except ImportError:
                pass  # toolkit not yet built
            return _JSONResponse(health)

        app.add_api_route("/health", _health, methods=["GET"])
        print("Custom /health endpoint registered")

    stop = result.get("stop") if isinstance(result, dict) else None
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        if stop:
            await stop()


if __name__ == "__main__":
    asyncio.run(main())
