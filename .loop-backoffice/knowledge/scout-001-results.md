# Scout 001 — Raw Search Results

Date: 2026-03-05
Queries run via Exa search. Results filtered for relevance.

---

## Query 1: "free REST API for AI agents useful tools 2024"

Notable hits:
- https://fast.io/resources/best-apis-autonomous-agents/ — curated list of agent-useful APIs
- https://aimlapi.com/best-ai-apis-for-free — AI model APIs with free tiers

## Query 2: "free public API OpenAPI specification developer"

Notable hits:
- https://github.com/public-apis/public-apis — massive curated list of free public APIs
- https://www.weather.gov/documentation/services-web-api — US NOAA weather, completely free

## Query 3: "API text extraction parsing free tier developer"

Notable hits:
- https://extractorapi.com/ — ExtractorAPI, 1000 free requests/month, article/PDF extraction
- https://parseur.com/blog/data-extraction-api — document parsing overview

## Query 4: "free weather API developer documentation"

Notable hits:
- https://open-meteo.com/en/docs — **No API key required**, high-res forecast, up to 16 days
- https://www.weatherapi.com/ — WeatherAPI.com, free tier with key, JSON/XML
- https://wttr.in/:help — wttr.in, completely free, no key, simple weather

## Query 5: "code execution API sandbox free tier"

Notable hits:
- https://e2b.dev/pricing — E2B: free hobby tier + $100 usage credits, sandbox for code execution
- https://simplesandbox.dev/ — SimpleSandbox, lightweight alternative

---

## Targeted Follow-Up Searches

### Open-Meteo
- URL: https://open-meteo.com/en/docs
- **No API key required** — completely free and open-source
- Forecast up to 16 days, hourly variables: temperature, wind, precipitation, humidity
- Simple REST: `https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m`
- Very clean docs, stable

### ip-api.com
- URL: https://ip-api.com/docs/api:json
- **No API key required**
- Geolocate any IP or domain: `http://ip-api.com/json/{ip}`
- Returns: country, region, city, lat/lon, timezone, ISP, org, AS
- Free tier: 45 requests/minute; HTTPS requires paid plan
- Very simple, well-documented

### E2B Code Execution Sandbox
- URL: https://e2b.dev/pricing
- Hobby tier: free + $100 one-time usage credits
- API key required (need from Mattie)
- Runs Python/JS/shell in isolated sandbox
- Used by Perplexity, Manus — production-grade
- Pricing: per compute-second (~$0.000014/s for CPU sandbox)

---

## Top Candidates for Evaluation

| API | Key Required | Free Limit | Use Case | Priority |
|-----|-------------|------------|----------|----------|
| Open-Meteo | No | Unlimited (free) | Weather for agents | HIGH |
| ip-api.com | No | 45 req/min | IP geolocation | HIGH |
| E2B | Yes | $100 credits | Code execution sandbox | MEDIUM |
| ExtractorAPI | Yes | 1000/month | Article text extraction | LOW (Exa already covers) |
| wttr.in | No | Unlimited | Simple weather | LOW (covered by Open-Meteo) |
