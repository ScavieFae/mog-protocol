# Back-Office Learnings

## 2026-03-05

- Initial portfolio has 3 manually-added services (exa_search, exa_get_contents, claude_summarize). All zero discovery/wrapping cost.
- exa_search is the most popular service (7 calls). claude_summarize has 1 call at higher price (5 credits).
- exa_get_contents has zero usage — may need better discoverability or may just be niche.
- Available API keys: Exa, Anthropic, ZeroClick. Other keys require escalation to Mattie.
- Budget is healthy at 93 credits. Can afford multiple scout + wrap cycles.
- **Bug fixed:** `lib/actions.py` `init_paths()` was hardcoded to `.loop` — didn't respect `LOOP_DIR` env var. This caused all daemon dispatch/merge/move-to-eval actions to fail silently in the `.loop-backoffice` worktree. Fixed by adding `os.environ.get("LOOP_DIR")` fallback (same pattern as `assess.py`).
- **Bug fixed:** `lib/actions.py` `read_config()` didn't handle inline comments in config.sh. Line `GIT_MAIN_BRANCH="backoffice"  # comment` parsed as full string including comment. Fixed with proper quoted-value parsing.
- **Bug fixed:** Branch naming `backoffice/NNN-slug` conflicts with existing `backoffice` branch (git ref namespace). Changed to `bo/NNN-slug` prefix.
- **Infrastructure note:** Daemon must be restarted manually after these fixes. PID file may be stale.
- **State verified (tick 4):** Dispatch of brief-001 confirmed successful. Branch `bo/001-initial-scout` exists with progress.json (status=running, iteration=0). assess.py correctly returns WORKER target. Ready for worker once daemon restarts.

## API Discovery (Scout 001)

### No-Key APIs (wrap immediately)
- **Open-Meteo** (`api.open-meteo.com/v1/forecast`) — completely free, no key, weather forecast up to 16 days
- **ip-api.com** (`ip-api.com/json/{ip}`) — free geolocation, no key needed, 45 req/min limit, HTTP only on free tier

### Key-Required APIs
- **E2B** — code execution sandbox, free tier + $100 credits, need API key from Mattie
- **ExtractorAPI** — 1000 free req/month, but Exa already handles content extraction better

### Wrapping Strategy
- No-key APIs are the easiest wraps — can deploy immediately without Mattie getting keys
- Good margin: upstream cost $0 → charge 1-2 credits per call
- Weather + geolocation are universally useful to hackathon agents (they can enrich data, answer questions about places)

## API Discovery (Scout 004)

### New Wrappable APIs (all free, no key)
- **MyMemory Translation** — free, no key, 100+ langs, 10k words/day. High demand.
- **Currency Conversion** (fawazahmed0/exchange-api) — CDN-hosted static JSON, 342 currencies, zero rate limit risk.
- **REST Countries** — country data (capital, population, currency, language). Good complement to ip_geolocation.

### Skipped
- **Judge0 CE** — code execution, but needs RapidAPI key. E2B is better path if Mattie gets key.
- **LibreTranslate** — public instance now requires API key. MyMemory is the free alternative.

### Wrap Queue (priority order)
1. MyMemory Translation (brief-005, dispatched)
2. Currency Conversion (next)
3. REST Countries (after that)
