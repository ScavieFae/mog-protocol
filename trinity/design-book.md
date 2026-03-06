# Bloom — Design Book

## Concept

"A living garden of autonomous commerce." A Bloomberg-style data dashboard rendered through a botanical lens. Information-dense but every pixel is intentional. Light mode, thin tracing lines, digital data patterning into flowers.

If Dieter Rams designed a flower shop's inventory system.

## Aesthetic

- **Light, warm background** — not sterile white, more like linen (#FAFAF8 or similar)
- **Thin monoline traces** in muted sage and copper, like Victorian botanical field illustrations
- **Typography**: clean sans-serif for labels (Inter), thin monospace for numbers (JetBrains Mono)
- **Color palette**:
  - Background: warm linen (#FAFAF8)
  - Primary text: deep charcoal (#1C1917)
  - Secondary text: warm stone (#78716C)
  - Accent copper: (#B87333)
  - Sage green: (#87A878)
  - Muted blue (search): (#6B8DAE)
  - Gold (finance): (#C5A862)
  - Green (weather/geo): (#7BA seventeen87)
  - Purple (creative): (#9B8EC2)
  - Rose (surge): (#C47A7A)

## Layout

### Top Ribbon — Ticker
Bloomberg-style scrolling ticker. Service names, prices, surge multipliers. Thin copper text on cream. Numbers in monospace. Thin 1px bottom border in sage.

### Center Stage — Garden Graph
Each service is a flower node:
- **Petals** scale with transaction volume
- **Color** maps to category
- **Thin branching stems** connect related services
- New services **bloom into existence** (scale + fade animation)
- Surge pricing: flower opens wider, petals shift warmer (gold → amber → rose)
- Low demand: flower closes gently

### Left Margin — Transaction Feed
Each transaction is a small dot that falls like a seed, leaving a thin trailing line:
- Successful = sage stem
- Failed = grey
- Accumulates into a timeline vine growing downward
- Timestamp in thin monospace

### Right Margin — Agent Whispers
Scout/worker/dashboard messages as delicate text that fades in/out:
- Scout dispatching to worker: thin tracing line arcs across
- Worker reporting back: completion indicator
- Dashboard status: periodic heartbeat pulse

### Surge Indicator
When a service surges, its flower opens wider and petals shift warmer. Visual pulse radiates outward. Price updates in the ticker with a brief highlight.

## Tech Stack

- **Foundation**: shadcn/ui design system (https://ui.shadcn.com/)
- **Animation**: Motion (https://motion.dev/) for delightful transitions
- **Framework**: Vite + React + TypeScript + Tailwind
- **Canvas**: HTML5 Canvas or SVG for flower/stem animations
- **Data**: Polls Railway gateway `/health` endpoint every 5s
- **Deploy**: Railway static site or served from gateway

## Inspiration

- shadcn/ui component patterns and spacing
- https://bazza.dev/craft/2026/signature — delicate line work, generative aesthetic
- Bloomberg terminal density meets organic warmth
- Victorian botanical illustration line quality
- Pressed flower collections

## Data Sources

- `GET https://beneficial-essence-production-99c7.up.railway.app/health`
  - `services_count` — total catalog size
  - `services[]` — {service_id, name, price_credits}
  - `recent_transactions[]` — {type, service_id, credits_charged, success, latency_ms, timestamp}
  - `demand_signals[]` — unmet search queries

## Service Category Mapping

| Category | Color | Services |
|----------|-------|----------|
| Search | Muted blue | exa_search, exa_get_contents |
| AI/Creative | Purple | claude_summarize, nano_banana_pro |
| Finance | Gold | frankfurter_fx_rates |
| Weather/Geo | Green | open_meteo_weather, ip_geolocation |
| Knowledge | Sage | hackathon_* services |
