# Brief: Service Detail Page

**Branch:** brief-014-service-detail-page
**Model:** sonnet

## Goal

Add a `/service/:id` page to the website that shows everything a viewer needs to know about a single service: what it does, how it's performing, pricing history, and how to buy it. This is the page you'd send someone to say "look at this."

## Context

Read these before starting:
- `web/src/App.tsx` — current routes: `/` (garden), `/colony` (trinity)
- `web/src/hooks/useHealth.ts` — health data types and fetcher
- `web/src/components/FlowerNode.tsx` — category colors and service categorization logic
- `web/src/pages/GardenPage.tsx` — for layout/style reference (linen bg, sage/copper palette)
- `trinity/design-book.md` — design language (Inter for labels, JetBrains Mono for numbers, botanical aesthetic)
- `src/gateway.py` `/health` endpoint — data source

## Tasks

1. **Add `/api/service/:id` data to the health endpoint (or a new endpoint).** The service detail page needs richer per-service data than `/health` currently provides. Two approaches — pick the simpler one:

   **Option A (preferred): Enrich `/health` per-service data.** Add to each service in the `/health` response:
   ```python
   {
       "service_id": "exa_search",
       "name": "Exa Web Search",
       "description": "Semantic web search...",
       "price_credits": 1,
       "current_price": 1,
       "surge_multiplier": 1.0,
       "provider": "mog-protocol",
       "example_params": {"query": "...", "max_results": 5},
       "stats": {
           "total_calls": 42,
           "successful_calls": 40,
           "failed_calls": 2,
           "success_rate": 0.95,
           "avg_latency_ms": 320,
           "first_seen": "2026-03-05T12:36:00Z",
           "last_called": "2026-03-06T03:15:00Z",
           "revenue_credits": 42
       }
   }
   ```
   Compute from telemetry: filter events by service_id, aggregate counts/latency/timestamps.

   **Option B: Add `/api/service/:id` endpoint.** Separate endpoint that returns the above for one service. Lighter on the health poll but requires a second fetch.

   Go with Option A unless it makes `/health` too heavy. The website already polls it.

2. **Create `ServiceDetailPage.tsx`.** Route: `/service/:id`. Layout (following design-book botanical aesthetic):

   **Header strip** — service name, category color dot, provider
   ```
   ● Exa Web Search                                  mog-protocol
   ```

   **Hero section** — the flower SVG for this service, rendered larger (reuse FlowerNode at bigger scale). Centered, with surge pulse visible if active.

   **Description card** — full description text. Below it, example params in a code block styled with JetBrains Mono.

   **Stats grid** — 2x3 grid of stat cards, each with:
   - Label (Inter, stone color)
   - Value (JetBrains Mono, copper/gold)

   Cards:
   | Uptime | Total Calls | Success Rate |
   | Revenue | Avg Latency | Current Price |

   **Uptime** = time since `first_seen`, displayed as "14h 23m" or "2d 6h".
   **Total Calls** = number, with successful/failed breakdown.
   **Success Rate** = percentage, green if >95%, amber if >80%, rose if <80%.
   **Revenue** = total credits earned by this service.
   **Avg Latency** = milliseconds.
   **Current Price** = credits with surge indicator if active.

   **Pricing section** — show base price, current surge multiplier, and a simple text explanation:
   - "Base price: 1cr"
   - "Surge: 1.5x (10 calls in last 15m)" or "No surge — stable pricing"

   **How to buy** — code snippet showing the MCP call:
   ```json
   {"method": "tools/call", "params": {"name": "buy_and_call", "arguments": {"service_id": "exa_search", "params": {"query": "your search", "max_results": 5}}}}
   ```

   **Back link** — "← back to garden" linking to `/`

3. **Make flowers clickable in Garden.** In `Garden.tsx` / `FlowerNode.tsx`, wrap each flower in a link to `/service/:id`. Use React Router's `Link`. The flower should have a subtle hover state (slight scale up or brightness increase).

4. **Add route in App.tsx.** Add `<Route path="/service/:id" element={<ServiceDetailPage />} />`.

5. **Create `useServiceDetail` hook (optional, or inline).** If using Option A, just filter the service from `useHealth` data by ID. If Option B, make a separate fetch.

## Completion Criteria

- [ ] `/service/:id` route exists and renders
- [ ] Page shows: name, description, example params, stats grid, pricing, how-to-buy
- [ ] Stats computed from health data: total calls, success rate, avg latency, revenue, uptime
- [ ] Flowers in garden are clickable links to detail page
- [ ] Visual style matches design book (linen bg, sage/copper palette, Inter + JetBrains Mono)
- [ ] Back link returns to garden

## Verification

- Navigate to `/service/exa_search` — page renders with real data
- Click a flower in the garden — navigates to detail page
- Stats section shows non-zero values (if gateway has transactions)
- Page looks correct with no services data (graceful empty state)
