"""Inter-agent message bus.

Implements the Trinity dispatch protocol: WRAP BRIEF, WRAP COMPLETE, WRAP FAILED,
and general inter-agent chatter. File-backed for persistence across restarts.
"""

import json
import os
import threading
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessageBus:
    def __init__(self, path: str = "data/agent_messages.json"):
        self._path = path
        self._lock = threading.Lock()
        self._messages: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._messages[-200:], f, indent=2)  # Keep last 200

    def send(self, from_agent: str, to_agent: str, content: str) -> dict:
        msg = {
            "id": len(self._messages),
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "timestamp": _now(),
            "read": False,
        }
        with self._lock:
            self._messages.append(msg)
            self._save()
        return msg

    def get_unread(self, agent_name: str) -> list[dict]:
        with self._lock:
            unread = [
                m for m in self._messages
                if m["to"] == agent_name and not m.get("read")
            ]
            for m in unread:
                m["read"] = True
            if unread:
                self._save()
            return unread

    def get_recent(self, n: int = 20) -> list[dict]:
        with self._lock:
            return list(self._messages[-n:])

    def get_conversation(self, agent_a: str, agent_b: str, n: int = 10) -> list[dict]:
        with self._lock:
            convos = [
                m for m in self._messages
                if (m["from"] in (agent_a, agent_b) and m["to"] in (agent_a, agent_b))
            ]
            return convos[-n:]


bus = MessageBus()
