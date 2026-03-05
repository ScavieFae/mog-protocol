# Wrap API into Mog Marketplace

You are adding a new API service to the Mog Protocol marketplace. Mattie (or another agent) has already evaluated this API and decided it's worth wrapping. Your job: write the handler, register it in the catalog, and test it. No judgment calls — just plumbing.

**Service to wrap:** $ARGUMENTS

---

## Before You Start

1. Read `src/services.py` — this is where all handlers and catalog registrations live. Follow the existing patterns exactly.
2. Read `src/catalog.py` — understand the `ServiceEntry` dataclass and `register()` signature.
3. Check `.env` for available API keys. If the key for this service isn't there, stop and report what key is needed.

## Step 1: Research the API (if needed)

If you don't already know the API's endpoints, auth, and response format, look it up. You need:
- The HTTP endpoint(s) or SDK method(s) to call
- Auth mechanism (header, body field, query param)
- Request format (JSON body fields, required vs optional)
- Response format (what fields come back, what to extract)

If there's a `docs/research/scout-*.md` file for this service, read it first — it has this info.

## Step 2: Write Handler Function(s)

Add to `src/services.py`, after the existing handlers. Follow this pattern exactly:

```python
def _service_name(param1: str, param2: int = 5) -> str:
    key = os.getenv("SERVICE_API_KEY")
    if not key:
        return json.dumps({"error": "SERVICE_API_KEY not set"})
    import httpx  # or the service's SDK
    resp = httpx.post("https://api.service.com/endpoint", json={
        "api_key": key,  # or use headers={"Authorization": f"Bearer {key}"}
        "param1": param1,
        "param2": param2,
    }, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return json.dumps({
        # Extract the useful fields. Keep it lean.
        "key_field": data["key_field"],
    })
```

Rules:
- Function name starts with `_` (private handler)
- Always check for the API key first, return error JSON if missing
- Import SDK/httpx inside the function (lazy import, avoids import-time failures)
- Always set `timeout=30` on HTTP calls
- Return a `json.dumps()` string — never return raw dicts or objects
- Extract only useful fields from the response. Buyer agents don't need raw API cruft.
- Keep handlers under 25 lines

## Step 3: Register in Catalog

Add catalog registrations in `src/services.py`, after the existing ones:

```python
catalog.register(
    service_id="service_name",          # snake_case, unique, what buy_and_call uses
    name="Human-Readable Name",         # shown in find_service results
    description="What it does. When/why an agent would use it.",  # this is searchable
    price_credits=N,                    # our pricing guidelines below
    example_params={"param1": "example value", "param2": 5},
    provider="mog-protocol",
    handler=_service_name,
)
```

### Pricing Guidelines
- **1 credit:** Simple lookups, searches, reads (fast, cheap upstream)
- **2 credits:** Content extraction, scraping, heavier reads
- **3-5 credits:** LLM calls, generation, multi-step operations
- **5-10 credits:** Expensive upstream calls, image generation, heavy compute
- General rule: upstream cost in dollars x 1000, minimum 1 credit

## Step 4: Test

Run the gateway tests to make sure nothing broke:
```bash
python -m src.test_gateway
```

Then test your new handler directly:
```python
from src.services import catalog
service = catalog.get("your_service_id")
result = service.handler(param1="test")
print(result)
```

If the API key is set, verify you get real results. If not, verify you get the error JSON.

## Step 5: Verify Gateway Integration

Confirm the new service shows up in catalog search:
```python
from src.services import catalog
results = catalog.search("your service description keywords")
print([r["service_id"] for r in results])
```

Your service should appear. No changes to `gateway.py` or `catalog.py` are needed — the gateway picks up new services automatically from `services.py`.

## Step 6: Report

When done, output:

```
WRAPPED: [service_id]
TOOLS ADDED: [comma-separated service_ids]
ENV VARS NEEDED: [KEY_NAME=description]
CREDITS: [service_id=N for each]
DEPENDENCIES: [any new pip packages, or "none"]
TEST: [pass/fail, brief note]
```

If you added a new pip dependency, also add it to `pyproject.toml` under `[project] dependencies`.

## What NOT to Do

- Don't modify `gateway.py` — it imports from `services.py` automatically
- Don't modify `catalog.py` — the dataclass and methods are stable
- Don't modify `server.py` — that's the direct MCP server, separate from the gateway
- Don't create new files — everything goes in `services.py`
- Don't over-engineer. One function per upstream endpoint. No classes, no abstractions.
