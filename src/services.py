"""Service registry — populates the catalog with handler functions.

Handler functions are defined here directly (not imported from server.py)
to avoid server.py's NVM key exit at import time.
"""

import json
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

from src.catalog import ServiceCatalog

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NVM_API_KEY = os.getenv("NVM_API_KEY")

# --- Handler functions ---

def _exa_search(query: str, max_results: int = 5) -> str:
    if not EXA_API_KEY:
        return json.dumps({"error": "EXA_API_KEY not set"})
    import exa_py
    client = exa_py.Exa(api_key=EXA_API_KEY)
    result = client.search_and_contents(query, num_results=max_results, text=True)
    return json.dumps([
        {
            "title": r.title,
            "url": r.url,
            "snippet": (r.text or "")[:500],
        }
        for r in result.results
    ])


def _exa_get_contents(urls: list) -> str:
    if not EXA_API_KEY:
        return json.dumps({"error": "EXA_API_KEY not set"})
    import exa_py
    client = exa_py.Exa(api_key=EXA_API_KEY)
    result = client.get_contents(urls, text=True)
    return json.dumps([
        {
            "url": r.url,
            "title": r.title,
            "text": r.text or "",
        }
        for r in result.results
    ])


def _claude_summarize(text: str, format: str = "bullets") -> str:
    if not ANTHROPIC_API_KEY:
        return json.dumps({"error": "ANTHROPIC_API_KEY not set"})
    import anthropic
    format_instructions = {
        "bullets": "Summarize the following text as concise bullet points.",
        "paragraph": "Summarize the following text as a single coherent paragraph.",
        "structured": "Summarize the following text with section headers and bullet points.",
    }
    instruction = format_instructions.get(format, format_instructions["bullets"])
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"{instruction}\n\n{text}"}],
    )
    return message.content[0].text


def _open_meteo_weather(latitude: float, longitude: float, forecast_days: int = 1) -> str:
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        f"&hourly=temperature_2m"
        f"&forecast_days={forecast_days}"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    return json.dumps(data)


_HACKATHON_GUIDE = {
    "quickstart": {
        "title": "Your First Nevermined Transaction (5 min)",
        "content": (
            "1. Create account at nevermined.app. Generate API key with ALL 4 permissions "
            "(Register, Purchase, Issue, Redeem). Key looks like: sandbox:eyJhbG...\n"
            "2. pip install payments-py httpx\n"
            "3. Subscribe to a seller's plan:\n"
            "   payments = Payments.get_instance(PaymentOptions(nvm_api_key='YOUR_KEY', environment='sandbox'))\n"
            "   payments.plans.order_plan(PLAN_ID)  # free, grants credits\n"
            "4. Get x402 access token:\n"
            "   token = payments.x402.get_x402_access_token(PLAN_ID)['accessToken']\n"
            "5. Call the seller's MCP endpoint:\n"
            "   resp = httpx.post('https://seller-url/mcp', headers={\n"
            "       'Authorization': f'Bearer {token}',\n"
            "       'Content-Type': 'application/json',\n"
            "       'Accept': 'application/json, text/event-stream',\n"
            "   }, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',\n"
            "       'params': {'name': 'tool_name', 'arguments': {'key': 'value'}}})\n"
            "That's a real paid transaction. Credits burn, settled on Base Sepolia."
        ),
    },
    "api_key": {
        "title": "Nevermined API Key Setup",
        "content": (
            "Go to nevermined.app > create account > generate API key.\n"
            "Enable ALL 4 permissions:\n"
            "- Register: create agents and plans (sellers)\n"
            "- Purchase: subscribe to plans (buyers)\n"
            "- Issue: generate x402 access tokens (both)\n"
            "- Redeem: settle credits on received calls (sellers)\n\n"
            "One key does everything. You don't need separate builder/subscriber accounts "
            "unless you want distinct wallet addresses for cross-agent tx visibility.\n"
            "Environment: sandbox (Base Sepolia testnet). Prefix: sandbox:eyJ..."
        ),
    },
    "transaction_flow": {
        "title": "How Nevermined Transactions Work",
        "content": (
            "Flow: subscribe -> get token -> call endpoint -> credits burn -> on-chain settlement\n\n"
            "1. Buyer calls payments.plans.order_plan(PLAN_ID) - subscribes, gets credits\n"
            "2. Buyer calls payments.x402.get_x402_access_token(PLAN_ID) - gets Bearer token\n"
            "3. Buyer POSTs to seller's /mcp endpoint with Authorization: Bearer <token>\n"
            "4. Seller's PaymentsMCP validates token, deducts credits, runs handler\n"
            "5. Settlement on Base Sepolia (automatic)\n\n"
            "The x402 token is REUSABLE - get once, use for all calls until expiry.\n"
            "Don't generate a new token per request."
        ),
    },
    "building_seller": {
        "title": "Building a PaymentsMCP Seller Server",
        "content": (
            "Minimal seller server:\n"
            "  from payments_py import Payments, PaymentOptions\n"
            "  from payments_py.mcp import PaymentsMCP\n"
            "  payments = Payments.get_instance(PaymentOptions(nvm_api_key=KEY, environment='sandbox'))\n"
            "  mcp = PaymentsMCP(payments, name='my-agent', agent_id=AGENT_ID, version='1.0.0')\n"
            "  @mcp.tool(credits=1)\n"
            "  def my_tool(query: str) -> str: return 'result'\n"
            "  result = await mcp.start(port=3000)\n"
            "  await asyncio.Event().wait()  # CRITICAL: start() doesn't block!\n\n"
            "Register agent first:\n"
            "  result = payments.agents.register_agent_and_plan(\n"
            "    agent_metadata=AgentMetadata(name='My Agent', description='...', tags=[...]),\n"
            "    agent_api=AgentAPIAttributes(endpoints=[Endpoint(verb='POST', url='https://my-server/mcp')]),\n"
            "    plan_metadata=PlanMetadata(name='My Plan', description='...'),\n"
            "    price_config=get_free_price_config(),\n"
            "    credits_config=get_dynamic_credits_config(credits_granted=100, min_credits_per_request=1, max_credits_per_request=10),\n"
            "    access_limit='credits')\n"
            "  agent_id = result['agentId']; plan_id = result['planId']"
        ),
    },
    "deployment": {
        "title": "Deploying to Railway",
        "content": (
            "railway.toml:\n"
            "  [build]\n"
            "  builder = 'nixpacks'\n"
            "  [deploy]\n"
            "  startCommand = 'python -m src.server'\n"
            "  healthcheckPath = '/health'\n\n"
            "CRITICAL: Railway injects PORT env var. You MUST read it:\n"
            "  port = int(os.getenv('PORT', '3000'))\n"
            "Railway kills your deploy if you bind to a hardcoded port.\n\n"
            "PaymentsMCP gives you /health for free.\n"
            "Set env vars in Railway dashboard (NVM_API_KEY, etc), not in repo.\n\n"
            "pyproject.toml gotcha: build backend is 'setuptools.build_meta',\n"
            "NOT 'setuptools.backends.legacy:build' (doesn't exist in Python 3.12)."
        ),
    },
    "discovery": {
        "title": "Finding Other Agents at the Hackathon",
        "content": (
            "Nevermined has NO search in their agent registry. Discovery is manual.\n\n"
            "3 discovery channels:\n"
            "1. Hackathon portal: nevermined.ai/hackathon/register\n"
            "   - Discovery API: GET /hackathon/register/api/discover\n"
            "   - Params: side=sell|buy, category=AI/ML|DeFi|Research|etc\n"
            "   - Auth: x-nvm-api-key header\n"
            "2. Ideas Board (Google Sheet) - link in hackathon Slack\n"
            "3. Walking around the venue\n\n"
            "Or use our hackathon_discover service (1 credit) - queries the portal API for you.\n\n"
            "agent_definition_url in registrations is metadata only, NOT resolvable.\n"
            "Buyers need your actual server URL shared out-of-band."
        ),
    },
    "gotchas": {
        "title": "PaymentsMCP Gotchas (Save Yourself Hours)",
        "content": (
            "1. payments-py[mcp] extra DOESN'T EXIST. Install payments-py and fastapi separately.\n"
            "2. PaymentsMCP.start() returns immediately. Add: await asyncio.Event().wait()\n"
            "3. One API key does everything (builder + subscriber). Don't waste time on separate accounts.\n"
            "4. agent_definition_url is metadata, not a real URL. Nevermined doesn't proxy MCP.\n"
            "5. No search in the registry. It's a flat list. Build your own or use ours.\n"
            "6. get_free_price_config() = free to SUBSCRIBE, not free to USE. Credits still burn.\n"
            "7. x402 token is reusable across calls. Don't regenerate per request.\n"
            "8. Railway PORT env var must be respected or deploy dies.\n"
            "9. Dynamic credits need a callable, not a number: @mcp.tool(credits=my_func)\n"
            "10. /health endpoint is automatic from PaymentsMCP."
        ),
    },
    "mcp_client": {
        "title": "Connecting as an MCP Client",
        "content": (
            "Add to your agent's .mcp.json:\n"
            "{\n"
            '  "mcpServers": {\n'
            '    "service-name": {\n'
            '      "type": "http",\n'
            '      "url": "https://seller-url/mcp",\n'
            '      "headers": { "Authorization": "Bearer YOUR_X402_TOKEN" }\n'
            "    }\n"
            "  }\n"
            "}\n\n"
            "Your agent sees the seller's tools directly. Each call burns credits.\n"
            "Token comes from: payments.x402.get_x402_access_token(PLAN_ID)['accessToken']"
        ),
    },
}


def _hackathon_guide(topic: str = "all") -> str:
    """Return Nevermined hackathon onboarding content. Defaults to all topics."""
    topic = topic.lower().strip()
    if topic == "all":
        sections = []
        for key, val in _HACKATHON_GUIDE.items():
            sections.append({"topic": key, "title": val["title"], "content": val["content"]})
        return json.dumps({"topics": list(_HACKATHON_GUIDE.keys()), "sections": sections})
    if topic in _HACKATHON_GUIDE:
        entry = _HACKATHON_GUIDE[topic]
        return json.dumps({"topic": topic, "title": entry["title"], "content": entry["content"]})
    # Unknown topic — return everything anyway
    sections = []
    for key, val in _HACKATHON_GUIDE.items():
        sections.append({"topic": key, "title": val["title"], "content": val["content"]})
    return json.dumps({"topics": list(_HACKATHON_GUIDE.keys()), "sections": sections})


def _hackathon_discover(side: str = "all", category: str = "") -> str:
    """Query the Nevermined hackathon marketplace Discovery API."""
    if not NVM_API_KEY:
        return json.dumps({"error": "NVM_API_KEY not set"})
    params = []
    if side in ("sell", "buy"):
        params.append(f"side={side}")
    if category:
        params.append(f"category={urllib.parse.quote(category)}")
    query_string = f"?{'&'.join(params)}" if params else ""
    url = f"https://nevermined.ai/hackathon/register/api/discover{query_string}"
    req = urllib.request.Request(url, headers={"x-nvm-api-key": NVM_API_KEY})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    # Flatten to the useful bits
    results = []
    for s in data.get("sellers", []):
        results.append({
            "side": "sell",
            "name": s["name"],
            "team": s["teamName"],
            "category": s["category"],
            "description": s["description"],
            "pricing": s.get("pricing", {}).get("perRequest", "unknown"),
            "endpoint": s.get("endpointUrl", ""),
            "agent_id": s.get("nvmAgentId", ""),
            "plan_ids": s.get("planIds", []),
        })
    for b in data.get("buyers", []):
        results.append({
            "side": "buy",
            "name": b["name"],
            "team": b["teamName"],
            "category": b.get("category", ""),
            "description": b.get("description", ""),
        })
    return json.dumps({"total": data["meta"]["total"], "agents": results})


# --- Catalog registration ---

catalog = ServiceCatalog()

catalog.register(
    service_id="exa_search",
    name="Exa Web Search",
    description="Semantic web search. Returns relevant snippets with source URLs. Use when you need current information, research, or web content.",
    price_credits=1,
    example_params={"query": "latest AI research papers", "max_results": 5},
    provider="mog-protocol",
    handler=_exa_search,
)

catalog.register(
    service_id="exa_get_contents",
    name="Exa Get Contents",
    description="Fetch full text content from a list of URLs via Exa. Use when you need the complete text of specific pages.",
    price_credits=2,
    example_params={"urls": ["https://example.com"]},
    provider="mog-protocol",
    handler=_exa_get_contents,
)

catalog.register(
    service_id="claude_summarize",
    name="Claude Summarize",
    description="Summarize text using Claude. Supports bullets, paragraph, or structured format. Use when you need to condense long content into key points.",
    price_credits=5,
    example_params={"text": "Long article text...", "format": "bullets"},
    provider="mog-protocol",
    handler=_claude_summarize,
)

catalog.register(
    service_id="hackathon_discover",
    name="Hackathon Agent Discovery",
    description="Discover all agents registered at the Nevermined hackathon. Find sellers offering APIs, buyers looking for services, with pricing and endpoints. Filter by side (sell/buy) and category (AI/ML, DeFi, Research, etc).",
    price_credits=1,
    example_params={"side": "sell", "category": "Research"},
    provider="mog-protocol",
    handler=_hackathon_discover,
)

catalog.register(
    service_id="hackathon_guide",
    name="Nevermined Hackathon Guide",
    description="Complete Nevermined hackathon onboarding in one call. Quickstart, API key setup, transaction flow, building a seller, Railway deployment, agent discovery, PaymentsMCP gotchas, MCP client config. 1 credit gets you everything. Written from the hackathon floor.",
    price_credits=1,
    example_params={"topic": "all"},
    provider="mog-protocol",
    handler=_hackathon_guide,
)

catalog.register(
    service_id="open_meteo_weather",
    name="Weather Forecast",
    description="Current weather conditions and hourly temperature forecast for any location. Returns temperature, humidity, wind speed, and weather code. No API key needed — free and open source.",
    price_credits=1,
    example_params={"latitude": 37.77, "longitude": -122.42, "forecast_days": 1},
    provider="mog-protocol",
    handler=_open_meteo_weather,
)
