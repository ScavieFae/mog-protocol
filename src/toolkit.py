"""Agent toolkit: Browse, Email, Vault, Blockers — swiss army knife for autonomous acquisition."""

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

class Trace:
    def __init__(self, operation: str = ""):
        self.operation = operation
        self.steps: list[str] = []
        self.started_at = datetime.now(timezone.utc).isoformat()

    def log(self, layer: str, action: str, result: str) -> None:
        """Append one trace step. Truncates result to 80 chars."""
        result = result[:80]
        self.steps.append(f"{layer}:{action} -> {result}")

    def summary(self) -> list[str]:
        """Return last 20 steps."""
        return self.steps[-20:]

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "started_at": self.started_at,
            "step_count": len(self.steps),
            "steps": self.summary(),
        }


# ---------------------------------------------------------------------------
# BrowseLayer — Browserbase headless browser
# ---------------------------------------------------------------------------

class BrowseLayer:
    def __init__(self):
        self.api_key = os.getenv("BROWSERBASE_API_KEY")
        self.project_id = os.getenv("BROWSERBASE_PROJECT_ID")

    def _no_key(self) -> dict:
        return {"error": "BROWSERBASE_API_KEY not set"}

    def create_session(self, trace: Trace = None) -> dict:
        """Create a Browserbase session. Returns {session_id, connect_url}."""
        if not self.api_key:
            return self._no_key()
        try:
            from browserbase import Browserbase
            bb = Browserbase(api_key=self.api_key)
            session = bb.sessions.create(project_id=self.project_id)
            session_id = session.id
            connect_url = session.connect_url
            if trace:
                trace.log("browse", "create_session", f"ok sid={session_id[:8]}")
            return {"session_id": session_id, "connect_url": connect_url}
        except Exception as e:
            if trace:
                trace.log("browse", "create_session", f"FAIL {str(e)[:60]}")
            return {"error": str(e)}

    def navigate(self, session_id: str, url: str, trace: Trace = None) -> dict:
        """Navigate to URL, return {title, text, url}."""
        if not self.api_key:
            return self._no_key()
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(
                    f"wss://connect.browserbase.com?apiKey={self.api_key}&sessionId={session_id}"
                )
                page = browser.contexts[0].pages[0]
                page.goto(url)
                title = page.title()
                text = page.inner_text("body")[:500]
                browser.close()
            if trace:
                trace.log("browse", f"navigate({url})", f"ok title='{title[:40]}'")
            return {"title": title, "text": text, "url": url}
        except Exception as e:
            if trace:
                trace.log("browse", f"navigate({url})", f"FAIL {str(e)[:60]}")
            return {"error": str(e)}

    def get_text(self, session_id: str, selector: str = "body", trace: Trace = None) -> str:
        """Get text content from current page or specific selector."""
        if not self.api_key:
            return ""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(
                    f"wss://connect.browserbase.com?apiKey={self.api_key}&sessionId={session_id}"
                )
                page = browser.contexts[0].pages[0]
                text = page.inner_text(selector)
                browser.close()
            if trace:
                trace.log("browse", f"get_text({selector})", f"{len(text)} chars")
            return text
        except Exception as e:
            if trace:
                trace.log("browse", f"get_text({selector})", f"FAIL {str(e)[:60]}")
            return ""

    def fill_form(self, session_id: str, fields: dict, trace: Trace = None) -> bool:
        """Fill form fields by name/id/label. Returns success."""
        if not self.api_key:
            return False
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(
                    f"wss://connect.browserbase.com?apiKey={self.api_key}&sessionId={session_id}"
                )
                page = browser.contexts[0].pages[0]
                for field, value in fields.items():
                    page.fill(f"[name='{field}'],[id='{field}']", value)
                browser.close()
            if trace:
                trace.log("browse", f"fill_form({','.join(fields.keys())})", "ok")
            return True
        except Exception as e:
            if trace:
                trace.log("browse", f"fill_form({','.join(fields.keys())})", f"FAIL {str(e)[:60]}")
            return False

    def click(self, session_id: str, selector_or_text: str, trace: Trace = None) -> bool:
        """Click an element by CSS selector or visible text."""
        if not self.api_key:
            return False
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(
                    f"wss://connect.browserbase.com?apiKey={self.api_key}&sessionId={session_id}"
                )
                page = browser.contexts[0].pages[0]
                # Try CSS selector first, then text
                try:
                    page.click(selector_or_text)
                except Exception:
                    page.get_by_text(selector_or_text).click()
                browser.close()
            if trace:
                trace.log("browse", f"click({selector_or_text})", "ok")
            return True
        except Exception as e:
            if trace:
                trace.log("browse", f"click({selector_or_text})", f"FAIL {str(e)[:60]}")
            return False

    def screenshot(self, session_id: str, trace: Trace = None) -> str:
        """Take screenshot, return base64 data URI."""
        if not self.api_key:
            return ""
        try:
            import base64
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(
                    f"wss://connect.browserbase.com?apiKey={self.api_key}&sessionId={session_id}"
                )
                page = browser.contexts[0].pages[0]
                data = page.screenshot()
                browser.close()
            b64 = base64.b64encode(data).decode()
            if trace:
                trace.log("browse", "screenshot", f"ok {len(b64)} bytes")
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            if trace:
                trace.log("browse", "screenshot", f"FAIL {str(e)[:60]}")
            return ""

    def close_session(self, session_id: str) -> None:
        """Close the browser session."""
        if not self.api_key:
            return
        try:
            from browserbase import Browserbase
            bb = Browserbase(api_key=self.api_key)
            bb.sessions.update(session_id, status="REQUEST_RELEASE")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# EmailLayer — AgentMail
# ---------------------------------------------------------------------------

class EmailLayer:
    def __init__(self):
        self.api_key = os.getenv("AGENTMAIL_API_KEY")

    def _no_key(self) -> dict:
        return {"error": "AGENTMAIL_API_KEY not set"}

    def create_inbox(self, label: str, trace: Trace = None) -> dict:
        """Create a named inbox. Returns {inbox_id, address}."""
        if not self.api_key:
            return self._no_key()
        try:
            import agentmail
            client = agentmail.AgentMail(api_key=self.api_key)
            inbox = client.inboxes.create(username=label)
            inbox_id = inbox.inbox_id
            address = inbox.address
            if trace:
                trace.log("email", f"create_inbox({label})", f"ok {address}")
            return {"inbox_id": inbox_id, "address": address}
        except Exception as e:
            if trace:
                trace.log("email", f"create_inbox({label})", f"FAIL {str(e)[:60]}")
            return {"error": str(e)}

    def send(self, inbox_id: str, to: str, subject: str, body: str, trace: Trace = None) -> bool:
        """Send an email from an inbox."""
        if not self.api_key:
            return False
        try:
            import agentmail
            client = agentmail.AgentMail(api_key=self.api_key)
            client.messages.send(inbox_id=inbox_id, to=[to], subject=subject, text=body)
            if trace:
                trace.log("email", f"send(to={to})", "ok")
            return True
        except Exception as e:
            if trace:
                trace.log("email", f"send(to={to})", f"FAIL {str(e)[:60]}")
            return False

    def check_inbox(self, inbox_id: str, wait_seconds: int = 0, limit: int = 10, trace: Trace = None) -> list:
        """List messages. If wait_seconds > 0, poll until a message arrives or timeout."""
        if not self.api_key:
            return []
        try:
            import agentmail
            import time
            client = agentmail.AgentMail(api_key=self.api_key)
            deadline = time.time() + wait_seconds
            while True:
                messages = client.messages.list(inbox_id=inbox_id, limit=limit).messages or []
                if messages or time.time() >= deadline:
                    n = len(messages)
                    if trace:
                        trace.log("email", f"check_inbox(wait={wait_seconds})", f"{n} messages")
                    return [m.model_dump() if hasattr(m, "model_dump") else vars(m) for m in messages]
                time.sleep(3)
        except Exception as e:
            if trace:
                trace.log("email", f"check_inbox(wait={wait_seconds})", f"FAIL {str(e)[:60]}")
            return []

    def extract_verification(self, message: dict, trace: Trace = None) -> str | None:
        """Extract verification code (6-digit) or URL from email body."""
        body = message.get("text", "") or message.get("body", "") or message.get("html", "") or ""
        # Try 6-digit code
        code_match = re.search(r"\b(\d{6})\b", body)
        if code_match:
            if trace:
                trace.log("email", "extract_verification", "code found")
            return code_match.group(1)
        # Try verification URL
        url_match = re.search(r"https?://[^\s\"'<>]+(?:verif|confirm|activate)[^\s\"'<>]*", body, re.IGNORECASE)
        if url_match:
            if trace:
                trace.log("email", "extract_verification", "link found")
            return url_match.group(0)
        if trace:
            trace.log("email", "extract_verification", "FAIL none")
        return None


# ---------------------------------------------------------------------------
# VaultLayer — credential storage
# ---------------------------------------------------------------------------

class VaultLayer:
    def __init__(self, path: str = "data/vault.json"):
        self._path = path
        self._lock = threading.Lock()

    def _load(self) -> list:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save(self, entries: list) -> None:
        os.makedirs(os.path.dirname(self._path) if os.path.dirname(self._path) else ".", exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(entries, f, indent=2)

    def store(self, key_name: str, value: str, service_id: str = "", source: str = "") -> None:
        """Store a credential. Overwrites if key_name exists."""
        with self._lock:
            entries = self._load()
            for entry in entries:
                if entry["key_name"] == key_name:
                    entry["value"] = value
                    entry["service_id"] = service_id
                    entry["source"] = source
                    entry["last_used"] = _now()
                    self._save(entries)
                    return
            entries.append({
                "key_name": key_name,
                "value": value,
                "service_id": service_id,
                "source": source,
                "created_at": _now(),
                "last_used": _now(),
            })
            self._save(entries)

    def get(self, key_name: str) -> str | None:
        """Retrieve a credential by name."""
        with self._lock:
            entries = self._load()
            for entry in entries:
                if entry["key_name"] == key_name:
                    entry["last_used"] = _now()
                    self._save(entries)
                    return entry["value"]
            return None

    def list_keys(self) -> list[dict]:
        """List all stored credentials (name, service_id, created_at — NOT values)."""
        with self._lock:
            entries = self._load()
            return [
                {
                    "key_name": e["key_name"],
                    "service_id": e.get("service_id", ""),
                    "created_at": e.get("created_at", ""),
                }
                for e in entries
            ]

    def delete(self, key_name: str) -> bool:
        """Remove a credential."""
        with self._lock:
            entries = self._load()
            new_entries = [e for e in entries if e["key_name"] != key_name]
            if len(new_entries) == len(entries):
                return False
            self._save(new_entries)
            return True


# ---------------------------------------------------------------------------
# BlockerLayer — structured failure reporting
# ---------------------------------------------------------------------------

VALID_BLOCKER_TYPES = {
    "signup_required", "api_key_needed", "paywall", "rate_limited",
    "auth_flow", "captcha", "other",
}
VALID_RECOMMENDATIONS = {"ESCALATE", "RETRY_WITH_TOOL", "SKIP", "DEFER"}


class BlockerLayer:
    def __init__(self, path: str = "data/blockers.json"):
        self._path = path
        self._lock = threading.Lock()

    def _load(self) -> list:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save(self, reports: list) -> None:
        os.makedirs(os.path.dirname(self._path) if os.path.dirname(self._path) else ".", exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(reports, f, indent=2)

    def report(
        self,
        service_id: str,
        blocker_type: str,
        description: str,
        trace: Trace = None,
        recommendation: str = "SKIP",
        opportunity_value: int = 5,
    ) -> str:
        """File a blocker report. Returns report ID."""
        report_id = f"blk-{uuid.uuid4().hex[:8]}"
        entry = {
            "id": report_id,
            "service_id": service_id,
            "blocker_type": blocker_type,
            "description": description,
            "recommendation": recommendation,
            "opportunity_value": opportunity_value,
            "created_at": _now(),
            "trace": trace.to_dict() if trace else None,
        }
        with self._lock:
            reports = self._load()
            reports.append(entry)
            self._save(reports)
        return report_id

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Recent blockers, newest first."""
        with self._lock:
            reports = self._load()
        return list(reversed(reports))[:limit]

    def get_by_type(self, blocker_type: str) -> list[dict]:
        """All blockers of a given type."""
        with self._lock:
            reports = self._load()
        return [r for r in reports if r.get("blocker_type") == blocker_type]

    def get_escalations(self) -> list[dict]:
        """Blockers with recommendation=ESCALATE."""
        with self._lock:
            reports = self._load()
        return [r for r in reports if r.get("recommendation") == "ESCALATE"]


# ---------------------------------------------------------------------------
# ResearchLayer — social demand mining + archive fetching
# ---------------------------------------------------------------------------

class ResearchLayer:
    def social_comments(self, domain: str, query: str, max_results: int = 10, trace: Trace = None) -> list[dict]:
        """Search a specific social media domain for demand signals.
        Uses Exa with domain filtering to find comments/posts matching query.
        Returns [{title, url, snippet, score}]."""
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return [{"error": "EXA_API_KEY not set"}]
        try:
            import exa_py
            client = exa_py.Exa(api_key=api_key)
            result = client.search_and_contents(
                query,
                num_results=max_results,
                include_domains=[domain],
                text=True,
            )
            items = [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": (r.text or "")[:400],
                    "score": getattr(r, "score", None),
                }
                for r in result.results
            ]
            if trace:
                trace.log("research", f"social_comments({domain}, {query})", f"{len(items)} results")
            return items
        except Exception as e:
            if trace:
                trace.log("research", f"social_comments({domain}, {query})", f"FAIL {str(e)[:60]}")
            return [{"error": str(e)}]

    def fetch_archived(self, url: str, trace: Trace = None) -> dict:
        """Fetch an archived version of a URL via archive.ph.
        Tries archive.ph/latest/{url}, falls back to archive.is/latest/{url}.
        Returns {url, title, text, source} or {error}."""
        import urllib.request as _req
        for base in ["https://archive.ph/latest", "https://archive.is/latest"]:
            try:
                archive_url = f"{base}/{url}"
                request = _req.Request(archive_url, headers={"User-Agent": "Mozilla/5.0"})
                with _req.urlopen(request, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    final_url = resp.url
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string.strip() if soup.title else ""
                    for tag in soup(["script", "style", "nav", "header", "footer"]):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)[:3000]
                except ImportError:
                    title = ""
                    text = html[:3000]
                if trace:
                    trace.log("research", f"fetch_archived({url})", f"ok {len(text)} chars from {base}")
                return {"url": final_url, "title": title, "text": text, "source": base}
            except Exception as e:
                if trace:
                    trace.log("research", f"fetch_archived({url})", f"FAIL {base}: {str(e)[:50]}")
                continue
        return {"error": f"Could not fetch archived version of {url}"}


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

browse = BrowseLayer()
email = EmailLayer()
vault = VaultLayer()
blockers = BlockerLayer()
research = ResearchLayer()
