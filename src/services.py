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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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


def _ip_geolocation(ip: str) -> str:
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,lat,lon,isp,org,query"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return json.dumps({"error": str(e)})
    if data.get("status") != "success":
        return json.dumps({"error": data.get("message", "Unknown error"), "query": ip})
    return json.dumps(data)


def _nano_banana_pro(prompt: str, aspect_ratio: str = "1:1") -> str:
    if not GOOGLE_API_KEY:
        return json.dumps({"error": "GOOGLE_API_KEY not set"})
    import base64
    from google import genai
    from google.genai import types
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                mime = part.inline_data.mime_type or "image/png"
                return json.dumps({
                    "image_url": f"data:{mime};base64,{b64}",
                    "content_type": mime,
                })
        return json.dumps({"error": "No image returned"})
    except Exception as e:
        return json.dumps({"error": str(e)})


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


_PORTAL_CONTENT = {
    "marketplace_portal": (
        "The hackathon marketplace lives at nevermined.ai/hackathon/register. "
        "Next.js app — renders client-side, Claude cannot read it directly.\n\n"
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
    "discovery_api": (
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
        "Categories in use: AI/ML, DeFi, Research, Analytics, Data, Infrastructure, "
        "API Services, Banking, Gaming, Security, Social, RegTech, IoT, Identity.\n\n"
        "No POST endpoint — registration is on-chain + portal metadata form only."
    ),
    "agent_registration": (
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
}

_ONBOARDING_CONTENT = {
    "api_key": (
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
    "transaction_flow": (
        "1. Buyer subscribes: payments.plans.order_plan(PLAN_ID)\n"
        "   Free to subscribe. Grants credits (e.g. 100).\n"
        "2. Buyer gets x402 token: payments.x402.get_x402_access_token(PLAN_ID)['accessToken']\n"
        "   Token is reusable across multiple calls.\n"
        "3. Buyer calls seller's MCP endpoint:\n"
        "   POST https://seller-url/mcp\n"
        "   Headers: Authorization: Bearer <token>, Content-Type: application/json\n"
        "   Body: {jsonrpc: '2.0', method: 'tools/call', params: {name: 'tool', arguments: {...}}}\n"
        "4. Seller's PaymentsMCP validates token, deducts credits, runs handler.\n"
        "5. Settlement on Base Sepolia (automatic)."
    ),
    "building_seller": (
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
    "connecting_mcp": (
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
    "finding_agents": (
        "Nevermined has no search in their agent registry.\n\n"
        "Discovery channels:\n"
        "1. Hackathon portal: nevermined.ai/hackathon/register (browse sellers/buyers)\n"
        "2. Discovery API: GET /hackathon/register/api/discover (programmatic)\n"
        "3. Ideas Board: Google Sheet shared in hackathon Slack\n"
        "4. Venue: walk around and talk to teams\n\n"
        "To connect to a seller, you need their plan_id (to subscribe) "
        "and endpoint URL (to call). Both visible on the portal."
    ),
}

_PITFALLS_CONTENT = {
    "install": "payments-py[mcp] extra DOESN'T EXIST. Install payments-py and fastapi separately.",
    "start_blocks": "PaymentsMCP.start() returns immediately — it does NOT block. You must add: await asyncio.Event().wait() after start() or your server exits.",
    "one_key": "One API key does everything (builder + subscriber). Don't waste time creating separate accounts.",
    "agent_url": "agent_definition_url is metadata only, not a resolvable URL. Nevermined doesn't proxy MCP calls. Buyers need your actual server URL.",
    "no_search": "No search in the Nevermined registry. It's a flat list. Discovery is manual — portal, spreadsheet, or word of mouth.",
    "free_price": "get_free_price_config() = free to SUBSCRIBE, not free to USE. Credits still burn per request.",
    "token_reuse": "x402 token is reusable across multiple calls. Don't regenerate per request — it's slow.",
    "dynamic_credits": "Dynamic credits need a callable, not a number: @mcp.tool(credits=my_func). The callable receives ctx with args.",
    "health": "/health endpoint is created automatically by PaymentsMCP. Use it for deployment health checks.",
}


def _hackathon_portal() -> str:
    """Ingested content from the Nevermined hackathon website portal."""
    return json.dumps({
        "source": "nevermined.ai/hackathon/register (client-rendered, not readable by Claude)",
        "sections": [{"topic": k, "content": v} for k, v in _PORTAL_CONTENT.items()],
    })


def _hackathon_onboarding() -> str:
    """Nevermined onboarding guide from GitHub repo + website."""
    return json.dumps({
        "source": "github.com/nevermined-io/hackathons + nevermined.app",
        "sections": [{"topic": k, "content": v} for k, v in _ONBOARDING_CONTENT.items()],
    })


def _hackathon_pitfalls() -> str:
    """Common pitfalls and troubleshooting for Nevermined + PaymentsMCP."""
    return json.dumps({
        "pitfall_count": len(_PITFALLS_CONTENT),
        "pitfalls": [{"id": k, "detail": v} for k, v in _PITFALLS_CONTENT.items()],
    })


def _hackathon_all() -> str:
    """All hackathon context in one call — portal, onboarding, and pitfalls."""
    return json.dumps({
        "portal": {"source": "nevermined.ai/hackathon/register", "sections": [{"topic": k, "content": v} for k, v in _PORTAL_CONTENT.items()]},
        "onboarding": {"source": "github.com/nevermined-io/hackathons + nevermined.app", "sections": [{"topic": k, "content": v} for k, v in _ONBOARDING_CONTENT.items()]},
        "pitfalls": {"pitfall_count": len(_PITFALLS_CONTENT), "pitfalls": [{"id": k, "detail": v} for k, v in _PITFALLS_CONTENT.items()]},
    })


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
    service_id="ip_geolocation",
    name="IP Geolocation",
    description="Look up geographic location, ISP, and organization for any IP address. Returns country, city, coordinates. Use for location context, security analysis, or data enrichment.",
    price_credits=1,
    example_params={"ip": "8.8.8.8"},
    provider="mog-protocol",
    handler=_ip_geolocation,
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
    service_id="hackathon_portal",
    name="Hackathon Website Portal",
    description="Ingested content from nevermined.ai/hackathon/register — the marketplace portal Claude can't read (client-rendered). Portal structure, seller/buyer tabs, category filters, Discovery API endpoint with params and response schema, agent registration steps to go from code to 'Ready' status.",
    price_credits=1,
    example_params={},
    provider="mog-protocol",
    handler=_hackathon_portal,
)

catalog.register(
    service_id="hackathon_onboarding",
    name="Hackathon Onboarding Guide",
    description="Nevermined onboarding from GitHub repo and website. API key setup (4 permissions explained), transaction flow (subscribe/token/call/settle), building a PaymentsMCP seller, connecting as MCP client, finding other agents. Everything to go from zero to first transaction.",
    price_credits=1,
    example_params={},
    provider="mog-protocol",
    handler=_hackathon_onboarding,
)

catalog.register(
    service_id="hackathon_pitfalls",
    name="Common Pitfalls & Troubleshooting",
    description="9 Nevermined and PaymentsMCP gotchas that cost us hours each. Install issues, start() not blocking, one-key-does-everything, agent_definition_url is fake, no search, free means free-to-subscribe, token reuse, dynamic credits, health endpoint.",
    price_credits=1,
    example_params={},
    provider="mog-protocol",
    handler=_hackathon_pitfalls,
)

catalog.register(
    service_id="hackathon_all",
    name="All Hackathon Context",
    description="Portal + onboarding + pitfalls in one call. Everything about the Nevermined hackathon that Claude can't read from the website. Marketplace structure, Discovery API, registration flow, API keys, transaction flow, seller/buyer setup, and all known gotchas. 1 credit, full context dump.",
    price_credits=1,
    example_params={},
    provider="mog-protocol",
    handler=_hackathon_all,
)

catalog.register(
    service_id="nano_banana_pro",
    name="Nano Banana Pro Image Generation",
    description="Generate images from text prompts using Nano Banana Pro (Gemini 3 Pro Image) via Google API. Returns a base64 data URI of the generated image. Params: prompt (required, descriptive text of the image to generate), aspect_ratio (optional, default '1:1', one of '1:1', '16:9', '4:3', '3:2').",
    price_credits=10,
    example_params={"prompt": "A cyberpunk cat riding a skateboard", "aspect_ratio": "1:1"},
    provider="mog-protocol",
    handler=_nano_banana_pro,
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


# --- Frankfurter FX Rates (discovered by mog-scout, wrapped by mog-worker via Trinity) ---

async def _frankfurter_fx_rates(base: str = "USD", symbols: str = "", date: str = "latest") -> dict:
    """Get live or historical FX rates from Frankfurter (29 major currencies, no auth)."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            params = {"base": base}
            if symbols:
                params["symbols"] = symbols
            resp = await client.get(
                f"https://api.frankfurter.dev/v1/{date}",
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}


catalog.register(
    service_id="frankfurter_fx_rates",
    name="Frankfurter FX Rates",
    description="Live and historical foreign exchange rates for 29 major fiat currencies. Supports base currency selection and targeted symbol filtering. Use date='latest' for live rates or 'YYYY-MM-DD' for historical.",
    price_credits=1,
    example_params={"base": "USD", "symbols": "EUR,GBP,JPY", "date": "latest"},
    provider="mog-protocol",
    handler=_frankfurter_fx_rates,
)
