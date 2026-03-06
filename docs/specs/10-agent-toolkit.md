# Spec 10: Agent Toolkit — Swiss Army Knife for Autonomous Acquisition

## What

A unified capability layer that sits between our scout/worker agents and the outside world. Not services to sell — *tools that let agents go get things*. Browse websites, receive email, sign up for accounts, store credentials, mine demand signals from social media, read paywalled articles, and report blockers when something doesn't work.

The key insight: agents today hit a wall when an API requires signup. They find a great opportunity, can't create an account, and have to escalate to a human. This toolkit removes that wall.

## Why

Our scout loop discovers APIs but gets blocked constantly:
- "Needs API key" → can't sign up without email
- "Requires account creation" → can't fill web forms
- "Pricing page is client-rendered" → can't read it
- "Article behind paywall" → can't evaluate the opportunity

With these tools, the agent can: browse → sign up → get verification email → extract API key → store it → wrap the API → sell it. End to end, no human needed.

This also feeds back into what we *sell*. If agents need these capabilities, other teams' agents do too. We can sell Browserbase sessions and AgentMail inboxes through our gateway.

## Architecture

```
Scout/Worker Agents
       |
  Agent Toolkit (src/toolkit.py)
       |
  ┌────┼────────┬──────────┬────────────┬──────────────┐
  |    |        |          |            |              |
Browse Email   Vault    Research    Blockers      Wallet
  |    |        |          |            |              |
Browserbase AgentMail  data/     Exa social    data/      Nevermined
              vault.json  archive.ph  blockers.json  (existing)
```

### Layer 1: Browse — Browserbase Integration

Headless browser for agents. Used internally for signup flows and page evaluation, and sold through gateway for other teams.

```python
# Internal use (scout evaluating a signup page):
from src.toolkit import browse
result = browse.navigate("https://api.example.com/signup")
result = browse.fill_form(session, {"email": "...", "password": "..."})
result = browse.click(session, "Submit")
result = browse.get_text(session)  # read the page

# Sold through gateway:
catalog.register(service_id="browser_navigate", ...)
```

**Env vars:** `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`
**Package:** `browserbase`, `playwright`

### Layer 2: Email — AgentMail Integration

Give agents email addresses. Used for account verification, API key delivery, newsletter signups for research.

```python
from src.toolkit import email
inbox = email.create_inbox("mog-scout")       # mog-scout@agentmail.to
email.send(inbox, to="signup@api.example.com", subject="Verify", body="...")
messages = email.check_inbox(inbox, wait=30)   # poll for verification email
code = email.extract_verification(messages[0]) # regex for 6-digit codes, links
```

**Env vars:** `AGENTMAIL_API_KEY`
**Package:** `agentmail`

### Layer 3: Credential Vault

When agents sign up for services, they get API keys. These need to be stored somewhere persistent and accessible across sessions.

```python
from src.toolkit import vault
vault.store("openweather_api_key", "abc123", source="signup via browserbase")
key = vault.get("openweather_api_key")
vault.list_keys()  # ["openweather_api_key", "newsapi_key", ...]
```

**Storage:** `data/vault.json` (gitignored). Each entry has:
```json
{
  "key_name": "openweather_api_key",
  "value": "abc123",
  "source": "signup via browserbase on 2026-03-06",
  "service_id": "openweather",
  "created_at": "2026-03-06T03:00:00Z",
  "last_used": "2026-03-06T04:00:00Z"
}
```

Thread-safe (same pattern as PortfolioManager). When a handler needs a key the agent acquired, it reads from vault instead of env vars.

### Layer 4: Research & Demand Mining

Tools that help the scout find *what to build next*.

**Exa Social Search:** Exa can search specific domains. Point it at a company's Instagram/Twitter to read what commenters are asking for.
```python
from src.toolkit import research
# What are people asking Nike for?
signals = research.social_comments("instagram.com/nike", "feature request OR wish OR need")
# What APIs are developers complaining about?
pain_points = research.social_comments("twitter.com", "API is broken OR need an API for")
```

Implementation: wraps our existing `_exa_search` with domain-filtered queries.

**Archive Access:** Fetch articles behind paywalls via archive.ph for market research.
```python
content = research.fetch_archived("https://nytimes.com/2026/03/05/tech/ai-agents.html")
# Tries: archive.ph/latest/{url} → archive.is/latest/{url} → original
```

Implementation: simple HTTP fetch to `https://archive.ph/latest/{url}`, parse with BeautifulSoup. No API key needed.

### Layer 5: Structured Blocker Reporting

When agents hit a wall, they shouldn't just say "blocked" in progress.json. They should file a structured blocker report that the conductor (and humans) can act on.

```python
from src.toolkit import blockers
blockers.report(
    service_id="stripe_api",
    blocker_type="signup_required",   # signup_required | api_key_needed | paywall | rate_limited | auth_flow | other
    description="Stripe requires business verification with EIN. Cannot complete signup autonomously.",
    attempted_steps=["browsed signup page", "filled email", "hit business verification wall"],
    recommendation="ESCALATE",         # ESCALATE | RETRY_WITH_TOOL | SKIP | DEFER
    opportunity_value=8,               # 1-10, how valuable this API would be if we could get it
)
```

**Storage:** `data/blockers.json` — array of blocker reports.

The conductor reads this file to:
1. Escalate high-value blockers to humans (e.g., "Stripe needs EIN — worth 8/10")
2. Retry with new toolkit capabilities (e.g., "now we have Browserbase, retry the signups that were blocked")
3. Feed demand signals (if we keep getting blocked by the same thing, maybe *that's* the service to sell)

### Layer 6: Agent Wallet (existing)

Our Nevermined portfolio manager (spec 09) already handles budget, spend/earn, and ROI decisions. The toolkit connects to it:
- Before signing up for a paid API: `portfolio.should_invest(cost, expected_revenue)`
- After acquiring an API key: `portfolio.spend(credits, service_id, "API signup fee")`
- When selling toolkit capabilities to others: `portfolio.earn(credits, service_id, "browserbase session sale")`

## Dual Use: Internal Tools + Sellable Services

Every toolkit capability has two faces:

| Toolkit Layer | Internal Use (scout/worker) | Sellable Service (gateway) |
|---|---|---|
| Browse | Evaluate signup pages, create accounts | `browser_navigate` — 5cr per session |
| Email | Receive verification codes | `agent_email` — 2cr to create inbox |
| Research | Find demand signals, read articles | `social_search` — 2cr, `archive_fetch` — 1cr |
| Blockers | Agent self-reporting | — (internal only) |

## What Gets Built (Brief Sequence)

### Brief 011: Toolkit Foundation
- Create `src/toolkit.py` as the unified module with submodules
- Browserbase integration: `browse.create_session()`, `browse.navigate()`, `browse.get_text()`, `browse.fill_form()`, `browse.click()`
- AgentMail integration: `email.create_inbox()`, `email.send()`, `email.check_inbox()`, `email.extract_verification()`
- Credential vault: `vault.store()`, `vault.get()`, `vault.list_keys()`
- Blocker reporting: `blockers.report()`, `blockers.get_recent()`, `blockers.get_by_type()`
- All backed by `data/vault.json` and `data/blockers.json`
- Tests for each sublayer

### Brief 012: Research Tools + Gateway Services
- Social demand mining via Exa domain-filtered search
- Archive.ph fetcher for paywalled articles
- Register sellable services in catalog: `browser_navigate`, `agent_email_inbox`, `social_search`, `archive_fetch`
- Update scout prompts: use toolkit for research, file blocker reports, check vault before escalating "needs API key"

## Dependencies

- `browserbase` + `playwright` (Browserbase)
- `agentmail` (AgentMail)
- `beautifulsoup4` (archive.ph parsing)
- Existing: `exa-py` (social search), `payments-py` (wallet)

## Env Vars

```
BROWSERBASE_API_KEY=<from browserbase.com dashboard>
BROWSERBASE_PROJECT_ID=<from browserbase.com dashboard>
AGENTMAIL_API_KEY=<from agentmail.to console>
```

## Credential Flow Example

Full autonomous API acquisition:

```
1. Scout finds "OpenWeather API" via Exa — free tier, 60 calls/min
2. Scout proposes hypothesis: "1cr to wrap, expect 15cr revenue"
3. portfolio.should_invest(1, 15) → True
4. Scout dispatches WRAP brief with "requires signup"

5. Worker reads brief, sees "requires signup"
6. browse.navigate("https://openweathermap.org/appid")
7. inbox = email.create_inbox("mog-openweather")
8. browse.fill_form(session, {"email": inbox.address, "password": generate()})
9. browse.click(session, "Create Account")
10. messages = email.check_inbox(inbox, wait=60)
11. link = email.extract_verification(messages[0])
12. browse.navigate(link)  # verify email
13. browse.navigate("https://home.openweathermap.org/api_keys")
14. api_key = browse.get_text(session, selector=".api-key")
15. vault.store("openweather_api_key", api_key, service_id="open_weather")

16. Worker writes handler in src/services.py using vault.get("openweather_api_key")
17. portfolio.spend(1, "open_weather", "wrapping cost")
18. portfolio.update_hypothesis(hyp_id, "wrapped")
19. Gateway picks up the new service automatically
```

If step 8 fails (e.g., CAPTCHA):
```
blockers.report(
    service_id="open_weather",
    blocker_type="signup_required",
    description="CAPTCHA on signup form. Browserbase can't solve it.",
    recommendation="ESCALATE",
    opportunity_value=7,
)
```

## Constraints

- Browserbase sessions cost money (~$0.01/session). Budget via portfolio.
- AgentMail is free tier to start. Watch for rate limits.
- archive.ph may rate-limit. Use sparingly, cache results.
- Credential vault is local JSON. If we need multi-agent access, move to a shared store later.
- For hackathon: focus on the *capability* existing. One successful autonomous signup is the demo moment.
