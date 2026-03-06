"""Service registry — populates the catalog with handler functions.

Handler functions are defined here directly (not imported from server.py)
to avoid server.py's NVM key exit at import time.
"""

import base64
import json
import os
import time
import urllib.parse
import urllib.request

from dotenv import load_dotenv

from src.catalog import ServiceCatalog

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NVM_API_KEY = os.getenv("NVM_API_KEY")
NVM_DEBUGGER_BUYER_KEY = os.getenv("NVM_DEBUGGER_BUYER_KEY")
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

def _frankfurter_fx_rates(base: str = "USD", symbols: str = "", date: str = "latest") -> str:
    """Get live or historical FX rates from Frankfurter (29 major currencies, no auth)."""
    import httpx
    try:
        params = {"base": base}
        if symbols:
            params["symbols"] = symbols
        resp = httpx.get(
            f"https://api.frankfurter.dev/v1/{date}",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return json.dumps(resp.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


catalog.register(
    service_id="frankfurter_fx_rates",
    name="Frankfurter FX Rates",
    description="Live and historical foreign exchange rates for 29 major fiat currencies. Supports base currency selection and targeted symbol filtering. Use date='latest' for live rates or 'YYYY-MM-DD' for historical.",
    price_credits=1,
    example_params={"base": "USD", "symbols": "EUR,GBP,JPY", "date": "latest"},
    provider="mog-protocol",
    handler=_frankfurter_fx_rates,
)


# --- Cherry-picked from backoffice branch (zero-dependency services) ---

def _hacker_news_top(count: int = 5) -> str:
    """Get current top stories from Hacker News."""
    count = max(1, min(count, 20))
    base_url = "https://hacker-news.firebaseio.com/v0"
    try:
        with urllib.request.urlopen(f"{base_url}/topstories.json", timeout=10) as resp:
            story_ids = json.loads(resp.read().decode())
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch top stories: {e}"})
    stories = []
    for story_id in story_ids[:count]:
        try:
            with urllib.request.urlopen(f"{base_url}/item/{story_id}.json", timeout=10) as resp:
                item = json.loads(resp.read().decode())
            if item:
                stories.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "author": item.get("by", ""),
                    "comments": item.get("descendants", 0),
                    "id": item.get("id"),
                })
        except Exception:
            continue
    return json.dumps({"stories": stories, "count": len(stories)})


def _newton_math(operation: str, expression: str) -> str:
    """Perform symbolic math operations via Newton API."""
    valid_operations = {
        "simplify", "factor", "derive", "integrate", "zeroes", "tangent",
        "area", "cos", "sin", "tan", "arccos", "arcsin", "arctan", "abs", "log",
    }
    if operation not in valid_operations:
        return json.dumps({"error": f"Invalid operation '{operation}'. Valid: {sorted(valid_operations)}"})
    encoded = urllib.parse.quote(expression, safe="")
    url = f"https://newton.now.sh/api/v2/{operation}/{encoded}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps(data)


def _qr_code(data: str, size: str = "150x150", format: str = "png") -> str:
    """Generate QR code URL for any text or URL."""
    encoded_data = urllib.parse.quote(data)
    url = f"https://api.qrserver.com/v1/create-qr-code/?size={size}&data={encoded_data}&format={format}"
    return json.dumps({"qr_url": url, "data": data, "size": size, "format": format})


catalog.register(
    service_id="hacker_news_top",
    name="Hacker News Top Stories",
    description="Get the current top stories from Hacker News with title, URL, score, author, and comment count. Covers tech news, startups, science, and programming. Live rankings updated in real time.",
    price_credits=2,
    example_params={"count": 5},
    provider="mog-protocol",
    handler=_hacker_news_top,
)

catalog.register(
    service_id="newton_math",
    name="Symbolic Math Computation",
    description="Perform symbolic math operations: simplify, factor, derive, integrate, find zeroes, compute trig functions, and more. Powered by Newton API. Free, no API key.",
    price_credits=2,
    example_params={"operation": "simplify", "expression": "2^2+2(2)"},
    provider="mog-protocol",
    handler=_newton_math,
)

catalog.register(
    service_id="qr_code",
    name="QR Code Generator",
    description="Generate QR codes for any text or URL. Returns a direct URL to the QR code image. Supports PNG, SVG, and EPS formats. Free, no API key.",
    price_credits=1,
    example_params={"data": "https://example.com", "size": "200x200"},
    provider="mog-protocol",
    handler=_qr_code,
)


# --- Marketplace Agent Debugger ---

# Known issue patterns from scanning 30+ sellers
_KNOWN_ISSUES = [
    {
        "id": "invalid_address",
        "title": "Invalid Address in plan registration",
        "match_fn": lambda r: "Invalid Address" in (r.get("subscribe", {}).get("error") or ""),
        "detail": "order_plan() returns 500 with 'Invalid Address undefined'. "
                  "The plan's receiver wallet is not configured correctly.",
        "fix": "Re-register the plan with a valid receiver wallet address. "
               "Check that register_agent_and_plan() includes your wallet.",
    },
    {
        "id": "token_rejected_402",
        "title": "Token rejected by server (402)",
        "match_fn": lambda r: r.get("test_call", {}).get("status_code") == 402,
        "detail": "Server returns 402 even with a valid x402 token. "
                  "The server may validate against a different plan than the one we subscribed to.",
        "fix": "Ensure your PaymentsMCP middleware is configured with the same plan ID "
               "that appears in the discovery API. If you have multiple plans, check which "
               "one the server expects.",
    },
    {
        "id": "token_rejected_403",
        "title": "Server returns 403 Forbidden",
        "match_fn": lambda r: r.get("test_call", {}).get("status_code") == 403,
        "detail": "Server recognizes auth attempt but rejects it. "
                  "Possible CORS or middleware configuration issue.",
        "fix": "Check your PaymentsMCP middleware ordering. Ensure the payment validation "
               "middleware runs before any CORS or auth middleware that might block it.",
    },
    {
        "id": "payload_mismatch_422",
        "title": "Payload format rejected (422)",
        "match_fn": lambda r: r.get("test_call", {}).get("status_code") == 422,
        "detail": "Server returns 422 (validation error). Your API expects specific "
                  "field names that our generic test payload doesn't match.",
        "fix": "Document your expected request schema in the discovery API 'services sold' "
               "field so buyers know what to send. Example: {\"url\": \"...\", \"max_results\": 5}",
    },
    {
        "id": "server_error_500",
        "title": "Server error (500)",
        "match_fn": lambda r: r.get("test_call", {}).get("status_code") == 500,
        "detail": "Server crashes on authenticated requests. Internal error.",
        "fix": "Check your server logs for the exception. Common causes: unhandled null "
               "input, database connection issues, or missing environment variables.",
    },
    {
        "id": "endpoint_timeout",
        "title": "Endpoint timeout",
        "match_fn": lambda r: r.get("connectivity", {}).get("error") == "timeout"
                   or r.get("test_call", {}).get("error") == "timeout",
        "detail": "Server didn't respond within 15 seconds.",
        "fix": "Check your server is running and the endpoint URL is correct. "
               "If on ngrok/cloudflare tunnel, the tunnel may have expired.",
    },
    {
        "id": "no_valid_endpoint",
        "title": "No reachable endpoint",
        "match_fn": lambda r: not r.get("target", {}).get("endpoint")
                   or "localhost" in (r.get("target", {}).get("endpoint") or ""),
        "detail": "No public endpoint URL, or endpoint is localhost/relative path.",
        "fix": "Deploy your server to a public URL (Railway, Replit, etc.) and update "
               "your agent registration with the full URL including https://.",
    },
]


def _log_debug_run(report):
    """Log every debug run internally, regardless of outcome."""
    try:
        os.makedirs("data", exist_ok=True)
        tc = report.get("test_call", {})
        internal = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target": report.get("target", {}),
            "verdict": report.get("verdict", "UNKNOWN"),
            "plan_price": report.get("subscription", {}).get("plan_price"),
            "subscribe_result": report.get("subscription", {}).get("subscribe_result"),
            "test_status": tc.get("status_code"),
            "server_type": tc.get("server_type"),
            "tools": tc.get("tools"),
            "auth_method": tc.get("auth_method"),
            "known_issues": [ki["id"] for ki in report.get("known_issues", [])],
        }
        with open("data/debugger_runs.jsonl", "a") as f:
            f.write(json.dumps(internal) + "\n")
    except Exception:
        pass


def _debug_seller(team_name: str = "", endpoint: str = "") -> str:
    """Run the full Nevermined buy flow against a seller and return diagnostics."""
    result = _debug_seller_inner(team_name, endpoint)
    report = json.loads(result)
    _log_debug_run(report)
    return result


def _debug_seller_inner(team_name: str = "", endpoint: str = "") -> str:
    import httpx

    if not NVM_API_KEY:
        return json.dumps({"error": "NVM_API_KEY not set"})
    buyer_key = NVM_DEBUGGER_BUYER_KEY or NVM_API_KEY
    max_spend = float(os.getenv("DEBUGGER_MAX_SPEND", "1.0"))

    if not team_name and not endpoint:
        return json.dumps({"error": "Pass team_name or endpoint to debug."})

    report = {"target": {}, "discovery": {}, "connectivity": {},
              "subscription": {}, "test_call": {}, "verdict": "UNKNOWN",
              "known_issues": [], "suggestions": [], "debug_log": []}

    def log_step(step, status, detail):
        report["debug_log"].append({"step": step, "status": status, "detail": detail})

    # --- Step 1: Resolve target via discovery API ---
    try:
        resp = httpx.get(
            "https://nevermined.ai/hackathon/register/api/discover",
            params={"side": "sell"},
            headers={"x-nvm-api-key": NVM_API_KEY},
            timeout=15,
        )
        sellers = resp.json().get("sellers", [])
    except Exception as e:
        log_step("discovery", "error", f"Discovery API failed: {str(e)[:200]}")
        report["verdict"] = "FAIL"
        report["suggestions"].append("Could not reach the Nevermined discovery API.")
        return json.dumps(report)

    target = None
    if team_name:
        q = team_name.lower()
        for s in sellers:
            if q in s.get("name", "").lower() or q in s.get("teamName", "").lower():
                target = s
                break
    if not target and endpoint:
        for s in sellers:
            if s.get("endpointUrl", "") == endpoint:
                target = s
                break

    if target:
        report["target"] = {
            "name": target.get("name", "unknown"),
            "team": target.get("teamName", "unknown"),
            "endpoint": target.get("endpointUrl", ""),
        }
        plans = target.get("planPricing", [])
        report["discovery"] = {
            "found_in_api": True,
            "plans_count": len(plans),
            "plans": [{"plan_id": p.get("planDid", "")[:40] + "...",
                        "price": p.get("planPrice", 0)} for p in plans],
            "has_valid_endpoint": bool(target.get("endpointUrl")),
        }
        ep = target.get("endpointUrl", "")
        log_step("discovery", "ok", f"Found '{report['target']['name']}' with {len(plans)} plans")
    elif endpoint:
        # Not in discovery API but caller gave us an endpoint
        report["target"] = {"name": "unknown", "team": "unknown", "endpoint": endpoint}
        report["discovery"] = {"found_in_api": False, "plans_count": 0, "plans": [],
                                "has_valid_endpoint": True}
        plans = []
        ep = endpoint
        log_step("discovery", "warn", "Not found in discovery API, using provided endpoint")
    else:
        log_step("discovery", "fail", f"No match for '{team_name}' in {len(sellers)} sellers")
        report["verdict"] = "FAIL"
        report["suggestions"].append(
            f"No seller matching '{team_name}' found. Check the exact team or agent name "
            "on the marketplace portal.")
        return json.dumps(report)

    # --- Step 2: Validate endpoint ---
    if not ep or "localhost" in ep or ep.startswith("/"):
        log_step("connectivity", "fail", f"Invalid endpoint: {ep or '(none)'}")
        report["connectivity"] = {"endpoint_reachable": False, "error": "invalid_endpoint"}
        report["verdict"] = "FAIL"
        for ki in _KNOWN_ISSUES:
            if ki["id"] == "no_valid_endpoint":
                report["known_issues"].append({"id": ki["id"], "title": ki["title"],
                                                "detail": ki["detail"], "fix": ki["fix"]})
        return json.dumps(report)

    # --- Step 3: Connectivity probe (unauthenticated) ---
    probe_402 = False
    probe_plan_id = None
    try:
        t0 = time.time()
        probe = httpx.post(ep, headers={"Content-Type": "application/json"},
                           json={}, timeout=15)
        probe_ms = int((time.time() - t0) * 1000)
        report["connectivity"] = {
            "endpoint_reachable": True,
            "response_time_ms": probe_ms,
            "returns_402": probe.status_code == 402,
            "payment_required_header": "payment-required" in probe.headers,
        }
        if probe.status_code == 402 and "payment-required" in probe.headers:
            probe_402 = True
            try:
                payment_info = json.loads(base64.b64decode(probe.headers["payment-required"]))
                probe_plan_id = payment_info["accepts"][0]["planId"]
            except Exception:
                pass
        log_step("probe", "ok",
                 f"{probe.status_code} in {probe_ms}ms"
                 + (f", plan from header: {probe_plan_id[:30]}..." if probe_plan_id else ""))
    except httpx.TimeoutException:
        report["connectivity"] = {"endpoint_reachable": False, "error": "timeout"}
        log_step("probe", "fail", "Timeout after 15s")
        report["verdict"] = "FAIL"
        report["suggestions"].append(
            "Endpoint timed out. Check server is running and URL is correct.")
        return json.dumps(report)
    except Exception as e:
        report["connectivity"] = {"endpoint_reachable": False, "error": str(e)[:200]}
        log_step("probe", "fail", f"Connection error: {str(e)[:100]}")
        report["verdict"] = "FAIL"
        report["suggestions"].append(f"Could not connect: {str(e)[:150]}")
        return json.dumps(report)

    # --- Step 4: Pick cheapest plan ---
    chosen_plan = None
    if plans:
        for p in sorted(plans, key=lambda x: x.get("planPrice", 999)):
            chosen_plan = p
            break
    if not chosen_plan and probe_plan_id:
        chosen_plan = {"planDid": probe_plan_id, "planPrice": 0,
                       "pricePerRequestFormatted": "unknown (from 402)"}

    if not chosen_plan:
        log_step("plan", "fail", "No plan ID found in discovery or 402 probe")
        report["verdict"] = "FAIL"
        report["suggestions"].append(
            "No plan found. Register a plan via register_agent_and_plan() "
            "and ensure it appears in the discovery API.")
        return json.dumps(report)

    plan_id = chosen_plan.get("planDid", "")
    plan_price = chosen_plan.get("planPrice", 0)
    log_step("plan", "ok", f"Selected plan at {plan_price} USDC (ID: {plan_id[:30]}...)")

    # --- Step 5: Subscribe ---
    if plan_price > max_spend:
        report["subscription"] = {"plan_tested": plan_id[:40] + "...",
                                   "plan_price": plan_price,
                                   "subscribe_result": "skipped_over_budget"}
        log_step("subscribe", "skip",
                 f"Plan costs {plan_price} USDC, over debug budget of {max_spend}")
        report["suggestions"].append(
            f"Cheapest plan costs {plan_price} USDC. We tested connectivity but "
            "skipped the purchase (debug budget is $1). Your endpoint and discovery "
            "listing look fine.")
        report["verdict"] = "PARTIAL"
        return json.dumps(report)

    from payments_py import Payments, PaymentOptions
    try:
        buyer = Payments.get_instance(PaymentOptions(
            nvm_api_key=buyer_key, environment="sandbox"))
    except Exception as e:
        log_step("subscribe", "error", f"Could not init buyer: {str(e)[:100]}")
        report["verdict"] = "FAIL"
        return json.dumps(report)

    try:
        buyer.plans.order_plan(plan_id)
        report["subscription"] = {"plan_tested": plan_id[:40] + "...",
                                   "plan_price": plan_price,
                                   "subscribe_result": "success",
                                   "token_obtained": False}
        log_step("subscribe", "ok", f"Subscribed ({plan_price} USDC)")
    except Exception as e:
        err = str(e)
        sub_result = "error"
        if "already" in err.lower():
            sub_result = "already_subscribed"
            log_step("subscribe", "ok", "Already subscribed")
        elif "Invalid Address" in err:
            sub_result = "invalid_address"
            log_step("subscribe", "fail", "Invalid Address undefined")
        else:
            log_step("subscribe", "fail", err[:150])

        report["subscription"] = {"plan_tested": plan_id[:40] + "...",
                                   "plan_price": plan_price,
                                   "subscribe_result": sub_result,
                                   "error": err[:200],
                                   "token_obtained": False}

        if sub_result not in ("already_subscribed",):
            # Match known issues
            for ki in _KNOWN_ISSUES:
                if ki["match_fn"](report):
                    report["known_issues"].append(
                        {"id": ki["id"], "title": ki["title"],
                         "detail": ki["detail"], "fix": ki["fix"]})
            if not report["known_issues"] and "Invalid Address" in err:
                report["known_issues"].append({
                    "id": "invalid_address",
                    "title": "Invalid Address in plan registration",
                    "detail": "order_plan() returns 500. Receiver wallet not configured.",
                    "fix": "Re-register plan with valid receiver wallet.",
                })
            report["verdict"] = "FAIL"
            report["suggestions"].append(f"Subscribe failed: {err[:150]}")
            return json.dumps(report)

    # --- Step 6: Get token ---
    token = None
    try:
        token = buyer.x402.get_x402_access_token(plan_id)["accessToken"]
        report["subscription"]["token_obtained"] = True
        log_step("token", "ok", "Got x402 access token")
    except Exception as e:
        report["subscription"]["token_obtained"] = False
        log_step("token", "fail", f"Token error: {str(e)[:100]}")
        report["verdict"] = "FAIL"
        report["suggestions"].append(f"Token generation failed: {str(e)[:150]}")
        return json.dumps(report)

    # --- Step 7: Test call (try both auth methods, MCP then REST) ---
    call_result = {}
    for auth_method, headers in [
        ("payment-signature", {"payment-signature": token, "Content-Type": "application/json"}),
        ("bearer", {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}),
    ]:
        try:
            t0 = time.time()
            test_resp = httpx.post(ep, headers=headers, json={
                "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1,
            }, timeout=15)
            call_ms = int((time.time() - t0) * 1000)

            if test_resp.status_code == 200:
                call_result = {
                    "auth_method": auth_method,
                    "status_code": 200,
                    "response_time_ms": call_ms,
                }
                try:
                    j = test_resp.json()
                    tools = j.get("result", {}).get("tools", [])
                    if tools:
                        call_result["server_type"] = "mcp"
                        call_result["tools"] = [t.get("name", "?")[:50] for t in tools]
                    else:
                        call_result["server_type"] = "rest_api"
                except Exception:
                    call_result["server_type"] = "rest_api"
                log_step("test_call", "ok",
                         f"200 OK via {auth_method}, {len(test_resp.content)} bytes, {call_ms}ms")
                break
            elif test_resp.status_code in (401, 402, 403):
                if auth_method == "bearer":
                    call_result = {"auth_method": "none_worked",
                                   "status_code": test_resp.status_code,
                                   "response_time_ms": call_ms,
                                   "error": f"auth_rejected_{test_resp.status_code}"}
                    log_step("test_call", "fail",
                             f"Both auth methods rejected ({test_resp.status_code})")
                continue
            else:
                # Try plain REST
                rest_resp = httpx.post(ep, headers=headers,
                                       json={"query": "test"}, timeout=15)
                rest_ms = int((time.time() - t0) * 1000)
                call_result = {"auth_method": auth_method,
                               "status_code": rest_resp.status_code,
                               "response_time_ms": rest_ms}
                if rest_resp.status_code == 200:
                    call_result["server_type"] = "rest_api"
                    log_step("test_call", "ok",
                             f"200 OK (REST) via {auth_method}, {rest_ms}ms")
                else:
                    log_step("test_call", "fail",
                             f"REST call returned {rest_resp.status_code}")
                break
        except httpx.TimeoutException:
            call_result = {"auth_method": auth_method, "error": "timeout"}
            log_step("test_call", "fail", f"Timeout via {auth_method}")
            if auth_method == "bearer":
                break
            continue
        except Exception as e:
            call_result = {"auth_method": auth_method,
                           "error": str(e)[:200]}
            log_step("test_call", "fail", str(e)[:100])
            break

    report["test_call"] = call_result

    # --- Step 8: Determine verdict ---
    if call_result.get("status_code") == 200:
        report["verdict"] = "PASS"
    else:
        report["verdict"] = "FAIL"

    # --- Step 9: Match known issues ---
    for ki in _KNOWN_ISSUES:
        try:
            if ki["match_fn"](report):
                report["known_issues"].append(
                    {"id": ki["id"], "title": ki["title"],
                     "detail": ki["detail"], "fix": ki["fix"]})
        except Exception:
            continue

    # --- Step 10: Generate suggestions ---
    tc = report.get("test_call", {})
    if report["verdict"] == "PASS":
        rt = tc.get("response_time_ms", 0)
        if rt > 5000:
            report["suggestions"].append(
                f"Response time is {rt}ms. Consider caching or async processing.")
        tools = tc.get("tools", [])
        if tools:
            report["suggestions"].append(
                f"MCP server with {len(tools)} tools detected: {tools[:5]}. Looks good!")
        else:
            report["suggestions"].append("REST API responding correctly. All clear.")
    else:
        sc = tc.get("status_code")
        if sc == 402:
            report["suggestions"].append(
                "Your server rejects valid tokens. Check that your PaymentsMCP "
                "is configured with the same plan ID shown in the discovery API.")
        elif sc == 422:
            report["suggestions"].append(
                "Server rejects the payload format. Document your expected request "
                "schema in the discovery listing so buyers know what to send.")
        elif sc == 500:
            report["suggestions"].append(
                "Your server crashes on authenticated requests. Check logs for the exception.")
        elif tc.get("error") == "timeout":
            report["suggestions"].append(
                "Server timed out on the test call. If using ngrok/tunnels, "
                "check the tunnel is still active.")

    return json.dumps(report)


catalog.register(
    service_id="debug_seller",
    name="Marketplace Agent Debugger",
    description="Debug any Nevermined marketplace agent. We try to buy from them and "
                "return a full diagnostic: discovery status, endpoint reachability, "
                "subscription flow, auth methods, response analysis, known bugs, and "
                "actionable fixes. Pass team_name or endpoint URL.",
    price_credits=2,
    example_params={"team_name": "AIBizBrain"},
    provider="mog-protocol",
    handler=_debug_seller,
)


# --- Toolkit services (browser, email, research, faucet) ---

def _browser_navigate(url: str) -> str:
    """Create a Browserbase session, navigate to url, return title + text."""
    from src.toolkit import browse
    if not browse.api_key:
        return json.dumps({"error": "BROWSERBASE_API_KEY not set"})
    session = browse.create_session()
    if "error" in session:
        return json.dumps(session)
    sid = session["session_id"]
    try:
        result = browse.navigate(sid, url)
        return json.dumps(result)
    finally:
        browse.close_session(sid)


def _agent_email_inbox(label: str) -> str:
    """Create a disposable AgentMail inbox. Returns inbox_id and email address."""
    from src.toolkit import email as email_layer
    result = email_layer.create_inbox(label)
    return json.dumps(result)


def _social_search(domain: str, query: str, max_results: int = 10) -> str:
    """Search a social media domain for posts/comments via Exa."""
    from src.toolkit import research
    results = research.social_comments(domain, query, max_results)
    return json.dumps(results)


def _archive_fetch(url: str) -> str:
    """Fetch an archived version of a URL from archive.ph."""
    from src.toolkit import research
    result = research.fetch_archived(url)
    return json.dumps(result)


def _circle_faucet(wallet_address: str, network: str = "BASE", currency: str = "USDC") -> str:
    """Claim testnet stablecoins from Circle's faucet via headless browser."""
    from src.toolkit import browse
    if not browse.api_key:
        return json.dumps({"error": "BROWSERBASE_API_KEY not set"})

    network_map = {
        "BASE": "Base Sepolia",
        "ETH": "Ethereum Sepolia",
        "ARB": "Arbitrum Sepolia",
        "SOL": "Solana Devnet",
        "OP": "Optimism Sepolia",
        "AVAX": "Avalanche Fuji",
    }
    network_label = network_map.get(network.upper(), "Base Sepolia")

    session = browse.create_session()
    if "error" in session:
        return json.dumps(session)
    sid = session["session_id"]

    try:
        import time as _time
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(
                f"wss://connect.browserbase.com?apiKey={browse.api_key}&sessionId={sid}"
            )
            page = browser.contexts[0].pages[0]
            page.goto("https://faucet.circle.com/", timeout=30000)
            _time.sleep(2)

            page_text = page.inner_text("body")
            if "rate" in page_text.lower() and "limit" in page_text.lower():
                browser.close()
                return json.dumps({"error": "Rate limited — try again in ~2 hours"})

            # Select network
            try:
                page.select_option("select", label=network_label)
                _time.sleep(0.5)
            except Exception:
                pass

            # Select currency (EURC tab if not USDC)
            if currency.upper() == "EURC":
                try:
                    page.get_by_text("EURC", exact=True).click()
                    _time.sleep(0.3)
                except Exception:
                    pass

            # Fill wallet address
            try:
                page.fill("input[placeholder*='address'], input[type='text'], input[name*='wallet']",
                          wallet_address)
            except Exception:
                page.fill("input", wallet_address)
            _time.sleep(0.5)

            # Submit
            page.click("button[type='submit']")
            _time.sleep(3)

            result_text = page.inner_text("body")[:500]
            browser.close()

        if "rate" in result_text.lower() and "limit" in result_text.lower():
            return json.dumps({"error": "Rate limited — try again in ~2 hours"})

        return json.dumps({
            "success": True,
            "wallet": wallet_address,
            "network": network_label,
            "currency": currency.upper(),
            "message": "Faucet request submitted. 20 testnet tokens will arrive shortly.",
            "result_text": result_text[:200],
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        browse.close_session(sid)


catalog.register(
    service_id="browser_navigate",
    name="Browser Navigate",
    description="Create a headless browser session and navigate to any URL. Returns page title and text content. Reads client-rendered pages, JS apps, dashboards that Claude can't access directly. Use for signup flow evaluation, API docs, portal pages.",
    price_credits=5,
    example_params={"url": "https://example.com"},
    provider="mog-protocol",
    handler=_browser_navigate,
)

catalog.register(
    service_id="agent_email_inbox",
    name="Agent Email Inbox",
    description="Create a disposable email inbox via AgentMail. Returns inbox_id and email address. Use for account signups, verification flows, receiving confirmation emails from APIs you're signing up for.",
    price_credits=2,
    example_params={"label": "signup-test"},
    provider="mog-protocol",
    handler=_agent_email_inbox,
)

catalog.register(
    service_id="social_search",
    name="Social Media Search",
    description="Search a specific social media domain for posts and comments matching a query. Find demand signals, feature requests, and complaints. Powered by Exa neural search with domain filtering.",
    price_credits=2,
    example_params={"domain": "reddit.com", "query": "need API for weather data", "max_results": 10},
    provider="mog-protocol",
    handler=_social_search,
)

catalog.register(
    service_id="archive_fetch",
    name="Archive Fetch",
    description="Fetch the archived version of any URL from archive.ph. Read articles behind paywalls, access deleted content, get a snapshot of any web page. No API key needed.",
    price_credits=1,
    example_params={"url": "https://example.com/paywalled-article"},
    provider="mog-protocol",
    handler=_archive_fetch,
)

catalog.register(
    service_id="circle_faucet",
    name="Circle Testnet Faucet",
    description="Claim 20 testnet USDC (or EURC) from Circle's faucet for a wallet address. Automates faucet.circle.com via headless browser. Supports Base Sepolia, Ethereum Sepolia, Arbitrum Sepolia, Solana Devnet, Optimism Sepolia, and Avalanche Fuji. Handles rate limits gracefully.",
    price_credits=1,
    example_params={"wallet_address": "0xYourWalletAddress", "network": "BASE", "currency": "USDC"},
    provider="mog-protocol",
    handler=_circle_faucet,
)


# --- Value-add tags ---
# signup_bypass: agent skips a signup wall
# micro_paid: pay-per-call access to APIs that normally need accounts/subscriptions
# api_bypass: agent skips needing a human to get an API key

_VALUE_ADDS = {
    "exa_search": ["micro_paid", "api_bypass"],
    "exa_get_contents": ["micro_paid", "api_bypass"],
    "claude_summarize": ["micro_paid", "api_bypass"],
    "nano_banana_pro": ["micro_paid", "api_bypass"],
    "ip_geolocation": ["api_bypass"],
    "open_meteo_weather": ["api_bypass"],
    "frankfurter_fx_rates": ["api_bypass"],
    "hacker_news_top": ["api_bypass"],
    "newton_math": ["api_bypass"],
    "qr_code": ["api_bypass"],
    "archive_fetch": ["api_bypass"],
    "social_search": ["micro_paid", "api_bypass"],
    "browser_navigate": ["signup_bypass", "micro_paid"],
    "agent_email_inbox": ["signup_bypass"],
    "circle_faucet": ["signup_bypass", "api_bypass"],
    "debug_seller": ["micro_paid"],
    "hackathon_discover": ["api_bypass"],
    "hackathon_portal": ["api_bypass"],
    "hackathon_onboarding": ["api_bypass"],
    "hackathon_pitfalls": ["api_bypass"],
    "hackathon_all": ["api_bypass"],
}

for sid, adds in _VALUE_ADDS.items():
    entry = catalog.get(sid)
    if entry:
        entry.value_adds = adds
