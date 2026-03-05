"""Service registry — populates the catalog with handler functions.

Handler functions are defined here directly (not imported from server.py)
to avoid server.py's NVM key exit at import time.
"""

import json
import os
import urllib.request

from dotenv import load_dotenv

from src.catalog import ServiceCatalog

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

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
    service_id="open_meteo_weather",
    name="Weather Forecast",
    description="Current weather conditions and hourly temperature forecast for any location. Returns temperature, humidity, wind speed, and weather code. No API key needed — free and open source.",
    price_credits=1,
    example_params={"latitude": 37.77, "longitude": -122.42, "forecast_days": 1},
    provider="mog-protocol",
    handler=_open_meteo_weather,
)
