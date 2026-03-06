# Brief: Agent Toolkit Foundation

**Branch:** brief-011-toolkit-foundation
**Model:** sonnet

## Goal

Create `src/toolkit.py` — the unified capability layer that lets our agents browse the web, manage email, store credentials, and file structured blocker reports. This is the swiss army knife that unblocks the "needs signup" wall.

## Context

Read these before starting:
- `docs/specs/10-agent-toolkit.md` — full spec with architecture, code examples, credential flow
- `src/services.py` — existing service handlers (for reference on style/patterns)
- `src/portfolio.py` — PortfolioManager (toolkit integrates with this for spend decisions)

## Tasks

1. **Create `src/toolkit.py` with four sublayers.** Single file, class-per-layer. Each layer is a module-level singleton.

   **BrowseLayer** — Browserbase headless browser:
   ```python
   class BrowseLayer:
       def __init__(self):
           self.api_key = os.getenv("BROWSERBASE_API_KEY")
           self.project_id = os.getenv("BROWSERBASE_PROJECT_ID")

       def create_session(self) -> dict:
           """Create a Browserbase session. Returns {session_id, connect_url}."""
           # Uses browserbase SDK

       def navigate(self, session_id: str, url: str) -> dict:
           """Navigate to URL, return {title, text, url}."""
           # Connects via Playwright CDP, navigates, extracts text

       def get_text(self, session_id: str, selector: str = "body") -> str:
           """Get text content from current page or specific selector."""

       def fill_form(self, session_id: str, fields: dict) -> bool:
           """Fill form fields by name/id/label. Returns success."""

       def click(self, session_id: str, selector_or_text: str) -> bool:
           """Click an element by CSS selector or visible text."""

       def screenshot(self, session_id: str) -> str:
           """Take screenshot, return base64 data URI."""

       def close_session(self, session_id: str) -> None:
           """Close the browser session."""
   ```
   If `BROWSERBASE_API_KEY` is not set, all methods return `{"error": "BROWSERBASE_API_KEY not set"}` (graceful degradation, same pattern as other services).

   **EmailLayer** — AgentMail:
   ```python
   class EmailLayer:
       def __init__(self):
           self.api_key = os.getenv("AGENTMAIL_API_KEY")

       def create_inbox(self, label: str) -> dict:
           """Create a named inbox. Returns {inbox_id, address}."""
           # client_id=f"mog-{label}" for idempotent retries

       def send(self, inbox_id: str, to: str, subject: str, body: str) -> bool:
           """Send an email from an inbox."""

       def check_inbox(self, inbox_id: str, wait_seconds: int = 0, limit: int = 10) -> list:
           """List messages. If wait_seconds > 0, poll until a message arrives or timeout."""
           # Returns [{from, subject, text, html, received_at}]

       def extract_verification(self, message: dict) -> str | None:
           """Extract verification code (6-digit) or URL from email body."""
           # Regex for: 6-digit codes, URLs containing verify/confirm/activate
   ```

   **VaultLayer** — Credential storage:
   ```python
   class VaultLayer:
       def __init__(self, path="data/vault.json"):
           # Same persistence pattern as PortfolioManager

       def store(self, key_name: str, value: str, service_id: str = "", source: str = "") -> None:
           """Store a credential. Overwrites if key_name exists."""

       def get(self, key_name: str) -> str | None:
           """Retrieve a credential by name."""

       def list_keys(self) -> list[dict]:
           """List all stored credentials (name, service_id, created_at — NOT values)."""

       def delete(self, key_name: str) -> bool:
           """Remove a credential."""
   ```
   File: `data/vault.json` (gitignored). Thread-safe with `threading.Lock`.

   **BlockerLayer** — Structured failure reporting:
   ```python
   class BlockerLayer:
       def __init__(self, path="data/blockers.json"):

       def report(self, service_id: str, blocker_type: str, description: str,
                  attempted_steps: list[str] = None, recommendation: str = "SKIP",
                  opportunity_value: int = 5) -> str:
           """File a blocker report. Returns report ID."""
           # blocker_type: signup_required | api_key_needed | paywall | rate_limited | auth_flow | captcha | other
           # recommendation: ESCALATE | RETRY_WITH_TOOL | SKIP | DEFER

       def get_recent(self, limit: int = 10) -> list[dict]:
           """Recent blockers, newest first."""

       def get_by_type(self, blocker_type: str) -> list[dict]:
           """All blockers of a given type."""

       def get_escalations(self) -> list[dict]:
           """Blockers with recommendation=ESCALATE."""
   ```
   File: `data/blockers.json` (gitignored). Thread-safe.

   Module-level singletons:
   ```python
   browse = BrowseLayer()
   email = EmailLayer()
   vault = VaultLayer()
   blockers = BlockerLayer()
   ```

2. **Ensure `data/` directory exists with `.gitkeep`, and add `data/vault.json` and `data/blockers.json` to `.gitignore`.** Portfolio JSON too if not already there.

3. **Create `src/test_toolkit.py` — tests for vault and blockers (no API keys needed).** Test:
   - Vault: store, get, list_keys (no values exposed), delete, overwrite, persistence round-trip
   - Blockers: report (returns ID), get_recent, get_by_type, get_escalations
   - BrowseLayer: test graceful degradation when no API key (returns error dict)
   - EmailLayer: test graceful degradation when no API key
   Skip tests that require live Browserbase/AgentMail connections (mark them or just don't write them — the env-missing graceful degradation test is sufficient).

## Completion Criteria

- [ ] `src/toolkit.py` exists with BrowseLayer, EmailLayer, VaultLayer, BlockerLayer
- [ ] All four singletons: `browse`, `email`, `vault`, `blockers`
- [ ] Graceful degradation: no crashes when API keys are missing
- [ ] `data/vault.json` and `data/blockers.json` gitignored
- [ ] `src/test_toolkit.py` passes for vault + blockers + graceful degradation
- [ ] Thread-safe persistence for vault and blockers

## Verification

- `python -m pytest src/test_toolkit.py -v` (or `python src/test_toolkit.py`)
- `python -c "from src.toolkit import browse, email, vault, blockers; print('All layers loaded')"` works
- `python -c "from src.toolkit import vault; vault.store('test', 'val'); assert vault.get('test') == 'val'; print('Vault works')"` works
