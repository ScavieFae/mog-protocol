"""Persistent agent with Anthropic conversation thread.

Each agent maintains a message history across ticks with compaction:
- Recent messages kept in full
- Older messages compacted into a summary
- System prompts from Trinity's design (trinity/*.md)

Uses Haiku for speed + cost. Configurable via MOG_AGENT_MODEL.
"""

import json
import os
import time
from datetime import datetime, timezone

import anthropic

from src.agents.tools import execute_tool

MODEL = os.getenv("MOG_AGENT_MODEL", "claude-haiku-4-5-20251001")
COMPACTION_MODEL = os.getenv("MOG_COMPACTION_MODEL", "claude-haiku-4-5-20251001")
MAX_RECENT_TURNS = int(os.getenv("MOG_MAX_RECENT_TURNS", "8"))  # Keep last N exchanges in full
MAX_TOOL_ROUNDS = int(os.getenv("MOG_MAX_TOOL_ROUNDS", "8"))
COMPACT_AFTER = int(os.getenv("MOG_COMPACT_AFTER", "16"))  # Compact when conversation exceeds this


class Agent:
    def __init__(self, name: str, role: str, system_prompt_template: str, tools: list[dict]):
        self.name = name
        self.role = role
        self._system_template = system_prompt_template  # Immutable template
        self.tools = tools
        self.messages: list[dict] = []  # Persistent conversation
        self._memory: str = ""  # Compacted summary of older conversation
        self.status = "idle"
        self.current_task: str | None = None
        self.recent_actions: list[str] = []
        self.activity_log: list[dict] = []  # Structured: {tool, args, result, timestamp, is_nvm}
        self.last_tick: str | None = None
        self.tick_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.last_tick_tokens = {"input": 0, "output": 0}
        self._client = anthropic.Anthropic()

    @property
    def system_prompt(self) -> str:
        """Build system prompt with current tick count injected."""
        prompt = self._system_template.replace("{{tick}}", str(self.tick_count))
        if self._memory:
            prompt += f"\n\nMEMORY FROM PREVIOUS TICKS:\n{self._memory}"
        return prompt

    def tick(self, context: str, incoming_messages: list[dict] | None = None) -> str:
        """Run one agent tick. Returns a summary of what happened."""
        self.status = "thinking"
        self.tick_count += 1
        self.last_tick = datetime.now(timezone.utc).isoformat()

        # Build the tick prompt
        parts = [f"[TICK {self.tick_count} — {self.last_tick}]"]
        parts.append(f"Current marketplace state:\n{context}")

        if incoming_messages:
            parts.append("\nMessages for you:")
            for m in incoming_messages:
                parts.append(f"  From {m['from']}: {m['content']}")

        parts.append("\nBased on your role and the current state, what should you do? Use your tools to take action.")

        self.messages.append({"role": "user", "content": "\n\n".join(parts)})

        # Compact old conversation if needed
        if len(self.messages) > COMPACT_AFTER:
            self._compact()

        # Run the agent with tool use loop
        summary_parts = []
        rounds = 0
        tick_input = 0
        tick_output = 0

        while rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            try:
                response = self._client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=self.system_prompt,
                    messages=self.messages,
                    tools=self.tools,
                )
            except Exception as e:
                error_msg = f"API error: {e}"
                self.status = "error"
                self.recent_actions.append(f"[error] {error_msg}")
                return error_msg

            # Track token usage
            usage = response.usage
            tick_input += usage.input_tokens
            tick_output += usage.output_tokens
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens

            # Process the response
            assistant_content = response.content
            self.messages.append({"role": "assistant", "content": _serialize_content(assistant_content)})

            # Check for tool use
            tool_uses = [b for b in assistant_content if b.type == "tool_use"]
            text_blocks = [b.text for b in assistant_content if b.type == "text" and b.text.strip()]

            for text in text_blocks:
                summary_parts.append(text)

            if not tool_uses:
                break

            # Execute tools and feed results back
            tool_results = []
            for tu in tool_uses:
                self.status = f"using {tu.name}"
                self.current_task = f"{tu.name}({_brief_args(tu.input)})"
                result = execute_tool(self.name, tu.name, tu.input)
                action = f"{tu.name}: {result[:120]}"
                self.recent_actions.append(action)
                is_creation = tu.name == "register_service" and "registered" in result.lower()
                self.activity_log.append({
                    "agent": self.name,
                    "tool": tu.name,
                    "args": _brief_args(tu.input),
                    "result": result[:200],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_nvm": tu.name in ("self_buy", "explore_seller", "discover_sellers"),
                    "is_scout": tu.name in ("scout_exa", "scout_apify", "scout_trustnet"),
                    "is_creation": is_creation,
                    "is_power_tool": tu.name in ("use_browser", "use_email", "use_search"),
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result,
                })

            self.messages.append({"role": "user", "content": tool_results})

        # Done
        self.status = "idle"
        self.current_task = None
        self.last_tick_tokens = {"input": tick_input, "output": tick_output}
        summary = "\n".join(summary_parts) if summary_parts else "(no text output)"

        # Keep recent_actions and activity_log bounded
        self.recent_actions = self.recent_actions[-20:]
        self.activity_log = self.activity_log[-50:]

        return summary

    def _compact(self) -> None:
        """Compact old conversation into a memory summary, keep recent turns."""
        # Find a clean cut point — must be a regular user text message (not tool_results)
        # so the remaining conversation is valid for the Anthropic API.
        target = max(0, len(self.messages) - MAX_RECENT_TURNS * 2)
        cut_point = target
        while cut_point < len(self.messages):
            msg = self.messages[cut_point]
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                break
            cut_point += 1

        if cut_point >= len(self.messages) - 2:
            return  # Can't find clean boundary, skip compaction

        old_msgs = self.messages[:cut_point]
        recent_msgs = self.messages[cut_point:]

        if not old_msgs:
            return

        # Build text summary of old messages for compaction
        old_text_parts = []
        for msg in old_msgs:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, str):
                old_text_parts.append(f"[{role}] {content[:300]}")
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            old_text_parts.append(f"[{role}] {block['text'][:200]}")
                        elif block.get("type") == "tool_use":
                            old_text_parts.append(f"[{role}] tool:{block['name']}({str(block.get('input', ''))[:100]})")
                        elif block.get("type") == "tool_result":
                            old_text_parts.append(f"[tool_result] {block.get('content', '')[:150]}")

        old_summary = "\n".join(old_text_parts[-20:])  # Last 20 entries from old section

        # Use Haiku to compact
        try:
            resp = self._client.messages.create(
                model=COMPACTION_MODEL,
                max_tokens=512,
                system="Summarize this agent conversation history into key facts and decisions. Be terse. Focus on: services proposed/registered, evaluations made, messages sent, key findings. Skip tool call details.",
                messages=[{"role": "user", "content": f"Previous memory:\n{self._memory}\n\nNew conversation to compact:\n{old_summary}"}],
            )
            self._memory = resp.content[0].text
        except Exception:
            # Fallback: just keep recent_actions as memory
            self._memory = f"Recent actions: {'; '.join(self.recent_actions[-10:])}"

        self.messages = recent_msgs

    def get_state(self) -> dict:
        """Serialize agent state for /health and the Board."""
        return {
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "current_task": self.current_task,
            "recent_actions": self.recent_actions[-10:],
            "tools": [t["name"] for t in self.tools],
            "last_tick": self.last_tick,
            "tick_count": self.tick_count,
            "tokens": {
                "total_input": self.total_input_tokens,
                "total_output": self.total_output_tokens,
                "last_tick_input": self.last_tick_tokens["input"],
                "last_tick_output": self.last_tick_tokens["output"],
                "estimated_cost_usd": round(
                    self.total_input_tokens * 0.80 / 1_000_000
                    + self.total_output_tokens * 4.00 / 1_000_000, 4
                ),
            },
            "conversation_length": len(self.messages),
            "has_memory": bool(self._memory),
            "activity_log": self.activity_log[-20:],
        }


def _serialize_content(content) -> list:
    """Serialize Anthropic content blocks for message persistence."""
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return result


def _brief_args(input_dict: dict) -> str:
    """Shorten tool args for display."""
    parts = []
    for k, v in list(input_dict.items())[:3]:
        sv = str(v)[:40]
        parts.append(f"{k}={sv}")
    return ", ".join(parts)
