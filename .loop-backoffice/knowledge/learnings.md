# Accumulated Learnings

## API Discovery

### No-Key APIs (wrap immediately)
- **Open-Meteo** (`api.open-meteo.com/v1/forecast`) — completely free, no key, weather forecast up to 16 days
- **ip-api.com** (`ip-api.com/json/{ip}`) — free geolocation, no key needed, 45 req/min limit, HTTP only on free tier

### Key-Required APIs
- **E2B** — code execution sandbox, free tier + $100 credits, need API key from Mattie
- **ExtractorAPI** — 1000 free req/month, but Exa already handles content extraction better

## Wrapping Strategy
- No-key APIs are the easiest wraps — can deploy immediately without Mattie getting keys
- Good margin: upstream cost $0 → charge 1-2 credits per call
- Weather + geolocation are universally useful to hackathon agents (they can enrich data, answer questions about places)
