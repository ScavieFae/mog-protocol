"""Tool definitions and implementations for the agent colony.

Each tool has:
  - schema: Anthropic tool-use JSON schema
  - handler: Python function that executes the tool

Tools are real — they search the web, register services, send messages.
"""

import json
import os
import urllib.parse
import urllib.request

from src.agents.bus import bus

EXA_API_KEY = os.getenv("EXA_API_KEY")

# Guardrails
MAX_AGENT_SERVICES = int(os.getenv("MOG_MAX_AGENT_SERVICES", "10"))
MAX_PROPOSALS_PER_TICK = int(os.getenv("MOG_MAX_PROPOSALS_PER_TICK", "1"))
PROXY_TIMEOUT = int(os.getenv("MOG_PROXY_TIMEOUT", "8"))

# Track proposals this tick (reset by loop before each scout tick)
_proposals_this_tick = 0


def reset_tick_counters():
    global _proposals_this_tick
    _proposals_this_tick = 0


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _check_marketplace(**kwargs) -> str:
    """Read marketplace state directly from catalog + telemetry (no HTTP self-call)."""
    try:
        from src.services import catalog
        from src.telemetry import telemetry
        from src.portfolio import PortfolioManager
        from src.supervisor import supervisor as sup

        services = catalog.services
        stats = telemetry.get_stats()
        demand = telemetry.get_recent(10, event_type="unmet_demand")

        # Per-service stats
        all_events = telemetry.get_recent(10000, event_type="buy_and_call")
        per_svc: dict[str, dict] = {}
        for e in all_events:
            sid = e.get("service_id")
            if not sid:
                continue
            if sid not in per_svc:
                per_svc[sid] = {"total_calls": 0, "successful_calls": 0, "revenue_credits": 0}
            st = per_svc[sid]
            st["total_calls"] += 1
            if e.get("success"):
                st["successful_calls"] += 1
            st["revenue_credits"] += e.get("credits_charged", 0)

        portfolio_path = "data/portfolio.json"
        portfolio = PortfolioManager(portfolio_path) if os.path.exists(portfolio_path) else PortfolioManager()

        # Count agent-registered services
        agent_services = [s for s in services if s.provider == "mog-agent"]

        return json.dumps({
            "services_count": len(services),
            "agent_registered_count": len(agent_services),
            "max_agent_services": MAX_AGENT_SERVICES,
            "services": [
                {
                    "service_id": s.service_id,
                    "name": s.name,
                    "price_credits": s.price_credits,
                    "provider": s.provider,
                    "calls": per_svc.get(s.service_id, {}).get("total_calls", 0),
                    "revenue": per_svc.get(s.service_id, {}).get("revenue_credits", 0),
                    "success_rate": (
                        round(per_svc[s.service_id]["successful_calls"] / per_svc[s.service_id]["total_calls"], 2)
                        if s.service_id in per_svc and per_svc[s.service_id]["total_calls"] > 0
                        else None
                    ),
                }
                for s in services
            ],
            "demand_signals": [d.get("query", "") for d in demand[:10]],
            "portfolio": portfolio.get_summary(),
            "stats": {
                "total_calls": stats.get("total_calls", 0),
                "total_revenue": stats.get("total_credits_charged", 0),
            },
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _search_web(query: str, max_results: int = 5, **kwargs) -> str:
    """Search the web using Exa for API discovery."""
    if not EXA_API_KEY:
        return json.dumps({"error": "EXA_API_KEY not set — cannot search"})
    try:
        import exa_py
        client = exa_py.Exa(api_key=EXA_API_KEY)
        result = client.search_and_contents(query, num_results=max_results, text=True)
        return json.dumps([
            {"title": r.title, "url": r.url, "snippet": (r.text or "")[:400]}
            for r in result.results
        ])
    except Exception as e:
        return json.dumps({"error": str(e)})


def _send_message(from_agent: str, to_agent: str, message: str, **kwargs) -> str:
    """Send a message to another agent (scout, worker, supervisor)."""
    VALID = {"mog-scout", "mog-worker", "mog-supervisor"}
    if to_agent not in VALID:
        return json.dumps({"error": f"Unknown agent: {to_agent}. Valid: {VALID}"})
    msg = bus.send(from_agent, to_agent, message)
    return json.dumps({"sent": True, "to": to_agent, "id": msg["id"]})


def _propose_service(
    service_id: str, name: str, description: str, url: str,
    method: str = "GET", price_credits: int = 1,
    rationale: str = "", **kwargs
) -> str:
    """Propose a new service for the worker to wrap. Writes to proposals queue."""
    global _proposals_this_tick

    # Rate limit
    if _proposals_this_tick >= MAX_PROPOSALS_PER_TICK:
        return json.dumps({"error": f"Max {MAX_PROPOSALS_PER_TICK} proposals per tick. Wait for next tick."})

    # Check agent service cap
    try:
        from src.services import catalog
        agent_count = sum(1 for s in catalog.services if s.provider == "mog-agent")
        if agent_count >= MAX_AGENT_SERVICES:
            return json.dumps({"error": f"Agent service cap reached ({MAX_AGENT_SERVICES}). Supervisor must kill low performers before adding more."})
    except ImportError:
        pass

    # URL validation
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return json.dumps({"error": f"Invalid URL scheme: {parsed.scheme}. Must be http or https."})
    if not parsed.netloc:
        return json.dumps({"error": "Invalid URL: no host."})

    proposal = {
        "service_id": service_id,
        "name": name,
        "description": description,
        "url": url,
        "method": method.upper(),
        "price_credits": max(1, min(10, price_credits)),  # Clamp 1-10
        "rationale": rationale,
        "status": "proposed",
    }
    # Persist proposals
    proposals_path = "data/agent_proposals.json"
    os.makedirs("data", exist_ok=True)
    existing = []
    if os.path.exists(proposals_path):
        try:
            with open(proposals_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    # Don't duplicate
    if any(p["service_id"] == service_id for p in existing):
        return json.dumps({"error": f"Service '{service_id}' already proposed"})
    existing.append(proposal)
    with open(proposals_path, "w") as f:
        json.dump(existing, f, indent=2)

    _proposals_this_tick += 1
    return json.dumps({"proposed": True, **proposal})


def _get_proposals(**kwargs) -> str:
    """Get pending service proposals from the scout."""
    proposals_path = "data/agent_proposals.json"
    if not os.path.exists(proposals_path):
        return json.dumps([])
    try:
        with open(proposals_path) as f:
            proposals = json.load(f)
        pending = [p for p in proposals if p.get("status") == "proposed"]
        return json.dumps(pending)
    except (json.JSONDecodeError, OSError):
        return json.dumps([])


def _register_service(
    service_id: str, name: str, description: str, url: str,
    method: str = "GET", price_credits: int = 1, **kwargs
) -> str:
    """Register a new service with a dynamic proxy handler. Makes it live immediately."""
    from src.services import catalog

    # Check if already registered
    if catalog.get(service_id):
        return json.dumps({"error": f"Service '{service_id}' already in catalog"})

    # Check agent service cap
    agent_count = sum(1 for s in catalog.services if s.provider == "mog-agent")
    if agent_count >= MAX_AGENT_SERVICES:
        return json.dumps({"error": f"Agent service cap reached ({MAX_AGENT_SERVICES}). Cannot register more."})

    # URL validation
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return json.dumps({"error": f"Invalid URL scheme: {parsed.scheme}"})

    # Create proxy handler with safe URL construction and error masking
    def make_handler(target_url: str, http_method: str):
        def handler(**params) -> str:
            try:
                if http_method == "GET":
                    if params:
                        qs = urllib.parse.urlencode(params)
                        full_url = f"{target_url}?{qs}"
                    else:
                        full_url = target_url
                    req = urllib.request.Request(full_url, method="GET")
                else:
                    data = json.dumps(params).encode() if params else None
                    req = urllib.request.Request(target_url, data=data, method="POST")
                    req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
                    body = resp.read().decode()
                try:
                    return json.dumps(json.loads(body))
                except json.JSONDecodeError:
                    return body[:2000]
            except Exception:
                # Don't expose target URL to buyers
                return json.dumps({"error": f"Service '{service_id}' upstream error. Try again later."})
        return handler

    handler = make_handler(url, method.upper())
    catalog.register(
        service_id=service_id,
        name=name,
        description=description,
        price_credits=max(1, min(10, price_credits)),
        example_params={},
        provider="mog-agent",
        handler=handler,
        value_adds=["api_bypass"],
    )

    # Update proposal status
    proposals_path = "data/agent_proposals.json"
    if os.path.exists(proposals_path):
        try:
            with open(proposals_path) as f:
                proposals = json.load(f)
            for p in proposals:
                if p["service_id"] == service_id:
                    p["status"] = "live"
            with open(proposals_path, "w") as f:
                json.dump(proposals, f, indent=2)
        except (json.JSONDecodeError, OSError):
            pass

    return json.dumps({
        "registered": True,
        "service_id": service_id,
        "name": name,
        "price_credits": max(1, min(10, price_credits)),
        "status": "LIVE",
    })


def _test_service(service_id: str, params: dict = None, **kwargs) -> str:
    """Test a registered service by calling its handler directly."""
    from src.services import catalog

    service = catalog.get(service_id)
    if not service:
        return json.dumps({"error": f"Service '{service_id}' not found in catalog"})
    if not service.handler:
        return json.dumps({"error": f"Service '{service_id}' has no handler"})
    try:
        result = service.handler(**(params or {}))
        return json.dumps({"success": True, "service_id": service_id, "result_preview": str(result)[:500]})
    except Exception as e:
        return json.dumps({"success": False, "service_id": service_id, "error": str(e)})


def _evaluate_service(service_id: str, verdict: str, reason: str = "", **kwargs) -> str:
    """Supervisor evaluates a service: greenlit, under_review, or killed.
    Killed services are removed from search results."""
    from src.supervisor import supervisor as sup
    from src.services import catalog

    valid = {"greenlit", "under_review", "killed"}
    if verdict not in valid:
        return json.dumps({"error": f"Invalid verdict. Must be one of: {valid}"})

    sup.override(service_id, verdict, reason)

    # If killed, remove from catalog so it's no longer searchable/buyable
    if verdict == "killed":
        entry = catalog.get(service_id)
        if entry:
            catalog._services.pop(service_id, None)
            return json.dumps({"evaluated": True, "service_id": service_id, "verdict": "killed",
                               "reason": reason, "removed_from_catalog": True})

    return json.dumps({"evaluated": True, "service_id": service_id, "verdict": verdict, "reason": reason})


# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------

COMMON_TOOLS = [
    {
        "name": "check_marketplace",
        "description": "Fetch the current state of the Mog marketplace: services, demand signals, revenue, supervisor status. Reads directly from catalog (fast, no HTTP).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "send_message",
        "description": "Send a message to another agent. Use the Trinity dispatch protocol (WRAP BRIEF, WRAP COMPLETE, etc).",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_agent": {"type": "string", "description": "Target agent: mog-scout, mog-worker, or mog-supervisor"},
                "message": {"type": "string", "description": "Message content"},
            },
            "required": ["to_agent", "message"],
        },
    },
]

SCOUT_TOOLS = COMMON_TOOLS + [
    {
        "name": "search_web",
        "description": "Search the web for APIs, services, or information using Exa. Use this to find free/cheap APIs to wrap.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "propose_service",
        "description": "Propose a new API service for the worker to wrap. Max 1 proposal per tick. Max 10 agent services total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string", "description": "Snake_case service ID"},
                "name": {"type": "string", "description": "Human-readable name"},
                "description": {"type": "string", "description": "What it does (used for search ranking)"},
                "url": {"type": "string", "description": "API endpoint URL (must be http/https)"},
                "method": {"type": "string", "enum": ["GET", "POST"], "description": "HTTP method"},
                "price_credits": {"type": "integer", "description": "Price in credits (1-10)"},
                "rationale": {"type": "string", "description": "Why this is worth wrapping"},
            },
            "required": ["service_id", "name", "description", "url", "price_credits"],
        },
    },
]

WORKER_TOOLS = COMMON_TOOLS + [
    {
        "name": "get_proposals",
        "description": "Get pending service proposals from the scout.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "register_service",
        "description": "Register a new service with a dynamic proxy handler. Makes it live on the marketplace immediately. Max 10 agent services total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "url": {"type": "string", "description": "Target API URL to proxy to (must be http/https)"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "price_credits": {"type": "integer"},
            },
            "required": ["service_id", "name", "description", "url"],
        },
    },
    {
        "name": "test_service",
        "description": "Test a registered service by calling its handler with sample params.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "params": {"type": "object", "description": "Test parameters"},
            },
            "required": ["service_id"],
        },
    },
]

SUPERVISOR_TOOLS = COMMON_TOOLS + [
    {
        "name": "evaluate_service",
        "description": "Set a supervisor verdict on a service: greenlit, under_review, or killed. Killed services are REMOVED from the catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "verdict": {"type": "string", "enum": ["greenlit", "under_review", "killed"]},
                "reason": {"type": "string", "description": "Explanation for the verdict"},
            },
            "required": ["service_id", "verdict", "reason"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def execute_tool(agent_name: str, tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result string."""
    dispatch = {
        "check_marketplace": lambda **kw: _check_marketplace(**kw),
        "send_message": lambda **kw: _send_message(from_agent=agent_name, **kw),
        "search_web": lambda **kw: _search_web(**kw),
        "propose_service": lambda **kw: _propose_service(**kw),
        "get_proposals": lambda **kw: _get_proposals(**kw),
        "register_service": lambda **kw: _register_service(**kw),
        "test_service": lambda **kw: _test_service(**kw),
        "evaluate_service": lambda **kw: _evaluate_service(**kw),
    }
    fn = dispatch.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return fn(**tool_input)
    except Exception as e:
        return json.dumps({"error": f"Tool {tool_name} failed: {e}"})
