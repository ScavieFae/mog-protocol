# Marketplace Feed — Missed Connections & Demand Signals

**Classification: SPECULATIVE (demo zing, not core functionality)**

## Concept

A live feed of marketplace activity — successful transactions, failed searches, price movements, agent behavior. Simultaneously entertainment (judges read it and laugh), market intelligence (teams see unfilled demand), and demand discovery (our wrapper agent reads it and fills gaps).

## Feed Events

### Missed Connections
Triggered when `find_service` returns 0 results:
```
🔍 "Looking for PDF-to-JSON extraction, budget 5 credits" — no matches found
   [3 agents searched for this in the last hour]
```

### Transactions
```
💰 team-4-agent bought exa-search-v1 for 3 credits (surge: 1.5x)
   [12th purchase of exa-search today]
```

### Price Movements
```
📈 exa-search-v1: 2 → 3 credits (surge pricing, 15 calls in last 15 min)
```

### New Listings
```
🆕 weatherstack-current listed at 2 credits/call
   "Get current weather for any location"
```

### Switching Behavior
```
🔄 team-7-agent switched from openai-embed-v1 to local-embed-v1 (cheaper)
```

## Implementation

WebSocket endpoint from the gateway server. Every logged event gets broadcast. Frontend is a simple HTML page with auto-scrolling feed — project on screen during demo.

```python
# In gateway server
from fastapi import WebSocket

@app.websocket("/feed")
async def feed(websocket: WebSocket):
    await websocket.accept()
    # Subscribe to event stream, broadcast as they happen
```

**Effort:** ~2 hours if the logging infrastructure exists (which it will from the pricing engine). The feed is a view over data we're already collecting.

## Demo Value

This is the backdrop for the 3-minute pitch. Scrolling feed on screen while presenting. Judges see real agent behavior happening live. The feed makes the marketplace feel alive in a way that a dashboard never could.

## Priority

P2. Don't build until the core (gateway + wrapper + pricing) works. But if we have Friday morning free, this is the highest-value demo polish.
