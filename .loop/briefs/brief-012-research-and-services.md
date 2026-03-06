# Brief: Research Tools + Sellable Toolkit Services

**Branch:** brief-012-research-and-services
**Model:** sonnet

## Goal

Add research capabilities to the toolkit (Exa social/demand mining, archive.ph for paywalled content), register sellable toolkit services in the gateway catalog, and update scout prompts to use the full toolkit.

## Context

Read these before starting:
- `docs/specs/10-agent-toolkit.md` — full spec, especially "Layer 4: Research & Demand Mining" and "Dual Use" table
- `src/toolkit.py` — toolkit module (created in brief-011)
- `src/services.py` — where to register new sellable services
- `.loop/prompts/conductor.md` — conductor prompt (needs toolkit awareness)
- `.loop/prompts/worker.md` — worker prompt (needs toolkit usage patterns)
- `.loop/knowledge/learnings.md` — add toolkit patterns here

## Tasks

1. **Add ResearchLayer to `src/toolkit.py`.** Two capabilities:

   **Social/demand mining via Exa:**
   ```python
   def social_comments(self, domain: str, query: str, max_results: int = 10) -> list[dict]:
       """Search a specific social media domain for demand signals.
       Uses Exa with domain filtering to find comments/posts matching query.
       Returns [{title, url, snippet, score}]."""
       # Wraps _exa_search with include_domains=[domain]
       # Uses exa_py.Exa search_and_contents with include_domains param
   ```

   **Archive.ph fetcher:**
   ```python
   def fetch_archived(self, url: str) -> dict:
       """Fetch an archived version of a URL via archive.ph.
       Tries archive.ph/latest/{url}, falls back to archive.is/latest/{url}.
       Returns {url, title, text, source} or {error}."""
       # HTTP GET to archive.ph/latest/{url}
       # Parse with BeautifulSoup, extract article text
       # No API key needed
   ```

   Add `research = ResearchLayer()` singleton.

2. **Register sellable toolkit services in `src/services.py`.** Four new services:

   **browser_navigate** (5 credits) — Create a Browserbase session and navigate to a URL. Returns page title and text content. Useful for reading client-rendered pages, checking signup flows, evaluating APIs. Params: `url` (required).

   **agent_email_inbox** (2 credits) — Create a disposable email inbox via AgentMail. Returns inbox ID and email address. Use for account signups, verification flows. Params: `label` (required, used as inbox name).

   **social_search** (2 credits) — Search a specific social media domain for posts/comments matching a query. Find demand signals, feature requests, complaints. Params: `domain` (required, e.g. "instagram.com/nike"), `query` (required), `max_results` (optional, default 10).

   **archive_fetch** (1 credit) — Fetch the archived version of a URL from archive.ph. Read articles behind paywalls. Params: `url` (required).

   Each handler function wraps the corresponding toolkit method, converts result to JSON string (matching existing handler patterns). Handle missing API keys gracefully (return error JSON, don't crash).

3. **Update `.loop/knowledge/learnings.md` — add toolkit section.** Practical guidance for the scout/worker:
   ```
   ## Agent Toolkit (src/toolkit.py)

   Available tools for autonomous API acquisition:
   - browse.navigate(url) — read any web page, even client-rendered
   - browse.fill_form(fields) / browse.click(selector) — complete signup flows
   - email.create_inbox(label) — get a working email address
   - email.check_inbox(inbox_id, wait_seconds=30) — poll for verification emails
   - email.extract_verification(message) — extract 6-digit codes or verify links
   - vault.store(name, value) / vault.get(name) — persist API keys across sessions
   - blockers.report(service_id, blocker_type, ...) — structured failure reporting
   - research.social_comments(domain, query) — mine demand signals from social media
   - research.fetch_archived(url) — read paywalled articles

   When blocked by signup:
   1. Check vault first — maybe a previous session already got the key
   2. Try browse + email flow
   3. If still blocked (CAPTCHA, etc.), file blocker report with recommendation=ESCALATE

   Blocker types: signup_required, api_key_needed, paywall, rate_limited, auth_flow, captcha, other
   Recommendations: ESCALATE (human needed), RETRY_WITH_TOOL (try toolkit), SKIP (not worth it), DEFER (try later)
   ```

4. **Update conductor prompt with toolkit awareness.** Add to `.loop/prompts/conductor.md`:
   - Read `data/blockers.json` for recent blockers during assessment
   - When a blocker has recommendation=RETRY_WITH_TOOL and we now have the toolkit, dispatch a retry brief
   - When dispatching scout briefs, remind worker that toolkit is available
   - Check `data/vault.json` — if worker acquired new keys, note in diary

5. **Add `beautifulsoup4` to `pyproject.toml` dependencies** (for archive.ph parsing).

## Completion Criteria

- [ ] ResearchLayer added to toolkit with social_comments + fetch_archived
- [ ] 4 new services registered in catalog: browser_navigate, agent_email_inbox, social_search, archive_fetch
- [ ] All handlers are sync, return JSON strings, handle missing keys gracefully
- [ ] learnings.md has toolkit section
- [ ] Conductor prompt reads blockers and vault
- [ ] beautifulsoup4 in dependencies
- [ ] `from src.services import catalog; len(catalog.services) >= 16` (12 existing + 4 new)

## Verification

- `python -c "from src.toolkit import research; print('Research layer loaded')"` works
- `python -c "from src.services import catalog; print(f'{len(catalog.services)} services')"` shows >= 16
- Read conductor prompt and confirm it references blockers.json and vault.json
