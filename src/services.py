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
    "marketplace": {
        "title": "Nevermined Hackathon Marketplace Portal",
        "content": (
            "The hackathon marketplace lives at nevermined.ai/hackathon/register. "
            "This is a Next.js app that reads from Nevermined's on-chain agent registry. "
            "Claude cannot read the portal directly — it renders client-side.\n\n"
            "What's on the portal:\n"
            "- Selling tab: all registered seller agents with name, team, category, "
            "description, endpoint URL, and price per request\n"
            "- Buying tab: buyer agents listing what services they need\n"
            "- Category filters: AI/ML, API Services, Banking, Data Analytics, DeFi, "
            "Gaming, Identity, Infrastructure, IoT, RegTech, Research, Security, Social\n"
            "- Each agent shows status: 'Ready' (fully registered) or 'Needs Metadata'\n"
            "- Agents show pricing as 'Free/req' or '$X.XX (Card)/req'\n\n"
            "To appear on the portal: register your agent on-chain via "
            "payments.agents.register_agent_and_plan(), then fill in the metadata form "
            "on the 'My Agents' tab (name, category, description, services list)."
        ),
    },
    "discovery_api": {
        "title": "Hackathon Discovery API",
        "content": (
            "Programmatic access to the marketplace portal data.\n\n"
            "Endpoint: GET https://nevermined.ai/hackathon/register/api/discover\n"
            "Auth: x-nvm-api-key header (your Nevermined API key)\n\n"
            "Query params:\n"
            "  side=sell    — only sellers\n"
            "  side=buy     — only buyers\n"
            "  category=AI%2FML  — filter by category (URL-encoded)\n\n"
            "Response shape:\n"
            "  { sellers: [{ name, teamName, category, description, pricing: { perRequest }, "
            "endpointUrl, nvmAgentId, planIds: [] }], "
            "buyers: [{ name, teamName, category, description }], "
            "meta: { total } }\n\n"
            "Categories seen: AI/ML, DeFi, Research, Analytics, Data, Infrastructure, "
            "API Services, Banking, Gaming, Security, Social, RegTech, IoT, Identity.\n\n"
            "No POST endpoint — registration is on-chain + portal metadata form only."
        ),
    },
    "agent_registration": {
        "title": "Registering an Agent on Nevermined",
        "content": (
            "Two steps to appear on the hackathon marketplace:\n\n"
            "Step 1 — On-chain registration (code):\n"
            "  from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata\n"
            "  from payments_py.plans import get_free_price_config, get_dynamic_credits_config\n"
            "  result = payments.agents.register_agent_and_plan(\n"
            "    agent_metadata=AgentMetadata(name='...', description='...', tags=[...]),\n"
            "    agent_api=AgentAPIAttributes(\n"
            "      endpoints=[Endpoint(verb='POST', url='https://your-server/mcp')],\n"
            "      agent_definition_url='https://your-server/mcp'),\n"
            "    plan_metadata=PlanMetadata(name='...', description='...'),\n"
            "    price_config=get_free_price_config(),\n"
            "    credits_config=get_dynamic_credits_config(\n"
            "      credits_granted=100, min_credits_per_request=1, max_credits_per_request=10),\n"
            "    access_limit='credits')\n"
            "  agent_id = result['agentId']; plan_id = result['planId']\n\n"
            "Step 2 — Portal metadata (browser):\n"
            "  Go to nevermined.ai/hackathon/register > My Agents tab.\n"
            "  Your on-chain agent appears with 'Needs Metadata' status.\n"
            "  Fill in: category, description, services (comma-separated), "
            "services per request description.\n"
            "  Endpoint URL and pricing are derived from your on-chain registration.\n"
            "  Save to flip status to 'Ready'."
        ),
    },
    "api_key": {
        "title": "Nevermined API Key Setup",
        "content": (
            "Go to nevermined.app > create account > generate API key.\n"
            "4 permission toggles — enable ALL of them:\n"
            "- Register: create agents and plans on the registry\n"
            "- Purchase: subscribe to other agents' plans\n"
            "- Issue: generate x402 access tokens for authenticated calls\n"
            "- Redeem: settle credits when buyers call your services\n\n"
            "One key with all 4 permissions works for both selling and buying.\n"
            "You don't need separate accounts unless you want distinct wallet addresses.\n"
            "Key format: sandbox:eyJhbGciOiJFUzI1NksifQ.eyJ...\n"
            "Environment: sandbox (Base Sepolia testnet)."
        ),
    },
    "transaction_flow": {
        "title": "How Nevermined Transactions Work",
        "content": (
            "1. Buyer subscribes: payments.plans.order_plan(PLAN_ID)\n"
            "   Free to subscribe. Grants credits (e.g. 100).\n"
            "2. Buyer gets x402 token: payments.x402.get_x402_access_token(PLAN_ID)['accessToken']\n"
            "   Token is reusable across multiple calls.\n"
            "3. Buyer calls seller's MCP endpoint:\n"
            "   POST https://seller-url/mcp\n"
            "   Headers: Authorization: Bearer <token>, Content-Type: application/json\n"
            "   Body: {jsonrpc: '2.0', method: 'tools/call', params: {name: 'tool', arguments: {...}}}\n"
            "4. Seller's PaymentsMCP validates token, deducts credits, runs handler.\n"
            "5. Settlement on Base Sepolia (automatic).\n\n"
            "get_free_price_config() means free to SUBSCRIBE, not free to use.\n"
            "Credits still burn per request. The plan costs $0 to join."
        ),
    },
    "building_seller": {
        "title": "Building a PaymentsMCP Seller",
        "content": (
            "pip install payments-py fastapi\n"
            "(payments-py[mcp] extra does NOT exist — install fastapi separately)\n\n"
            "  from payments_py.mcp import PaymentsMCP\n"
            "  mcp = PaymentsMCP(payments, name='my-agent', agent_id=AGENT_ID, version='1.0.0')\n"
            "  @mcp.tool(credits=1)\n"
            "  def my_tool(query: str) -> str: return 'result'\n"
            "  result = await mcp.start(port=3000)\n"
            "  await asyncio.Event().wait()  # start() returns immediately!\n\n"
            "Dynamic pricing: pass a callable instead of int:\n"
            "  def price_fn(ctx): return lookup(ctx['args']['service_id'])\n"
            "  @mcp.tool(credits=price_fn)\n\n"
            "PaymentsMCP auto-creates /health endpoint.\n"
            "agent_definition_url is metadata only — not a resolvable URL."
        ),
    },
    "discovery": {
        "title": "Finding Other Agents",
        "content": (
            "Nevermined has no search in their agent registry.\n\n"
            "Discovery channels:\n"
            "1. Hackathon portal: nevermined.ai/hackathon/register (browse sellers/buyers)\n"
            "2. Discovery API: GET /hackathon/register/api/discover (programmatic, see discovery_api topic)\n"
            "3. Ideas Board: Google Sheet shared in hackathon Slack\n"
            "4. Venue: walk around and talk to teams\n\n"
            "To connect to a seller, you need their plan_id (to subscribe) "
            "and endpoint URL (to call). Both visible on the portal."
        ),
    },
    "mcp_client": {
        "title": "Connecting to a Seller via MCP",
        "content": (
            "Add to your agent's .mcp.json:\n"
            '  { "mcpServers": { "service": { "type": "http",\n'
            '    "url": "https://seller-url/mcp",\n'
            '    "headers": { "Authorization": "Bearer YOUR_X402_TOKEN" } } } }\n\n'
            "Get the token:\n"
            "  from payments_py import Payments, PaymentOptions\n"
            "  payments = Payments.get_instance(PaymentOptions(nvm_api_key=KEY, environment='sandbox'))\n"
            "  payments.plans.order_plan(PLAN_ID)  # subscribe first\n"
            "  token = payments.x402.get_x402_access_token(PLAN_ID)['accessToken']\n\n"
            "Your agent sees the seller's tools directly. Each call burns credits."
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
    description="Ingested content from the Nevermined hackathon portal, marketplace, and registration flow — the parts Claude can't read directly. Covers: marketplace portal structure, Discovery API with endpoint/params/response schema, agent registration steps, API key permissions, transaction flow, and how to connect as buyer or seller. 1 credit for everything.",
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
