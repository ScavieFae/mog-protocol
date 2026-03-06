"""Helicone observability logging for the Mog gateway."""

import base64
import json as _json
import os
import time
import threading
from typing import Any

import httpx

NVM_API_KEY = os.getenv("NVM_API_KEY", "")
HELICONE_API_KEY = ""
ACCOUNT_ADDRESS = ""

# Extract helicone key from JWT payload (no PyJWT dependency needed)
try:
    token = NVM_API_KEY.replace("sandbox:", "").replace("production:", "")
    payload_b64 = token.split(".")[1]
    # Add padding
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    claims = _json.loads(base64.urlsafe_b64decode(payload_b64))
    HELICONE_API_KEY = claims.get("o11y", "")
    ACCOUNT_ADDRESS = claims.get("sub", "")
except Exception:
    pass

HELICONE_LOGGING_URL = os.getenv(
    "HELICONE_LOGGING_URL",
    "https://helicone.nevermined.dev/jawn/v1/trace/custom/v1/log",
)


def log_tool_call(
    agent_id: str,
    plan_id: str,
    service_id: str,
    service_name: str,
    params: dict,
    result: Any,
    credits_charged: int,
    latency_ms: int,
    success: bool,
    surge_multiplier: float = 1.0,
    subscriber_address: str = "",
) -> None:
    """Fire-and-forget log of a tool call to Helicone. Runs in a background thread."""
    if not HELICONE_API_KEY:
        return

    def _send():
        try:
            now = time.time()
            start = now - (latency_ms / 1000)

            headers = {
                "Authorization": f"Bearer {HELICONE_API_KEY}",
                "Content-Type": "application/json",
                "Helicone-Auth": f"Bearer {HELICONE_API_KEY}",
                "Helicone-Property-accountAddress": ACCOUNT_ADDRESS,
                "Helicone-Property-consumerAddress": subscriber_address or "self-buy",
                "Helicone-Property-agentId": agent_id,
                "Helicone-Property-planId": plan_id,
                "Helicone-Property-agentName": "mog-gateway",
                "Helicone-Property-environmentName": os.getenv("NVM_ENVIRONMENT", "sandbox"),
                "Helicone-Property-serviceId": service_id,
                "Helicone-Property-serviceName": service_name,
                "Helicone-Property-creditsCharged": str(credits_charged),
                "Helicone-Property-surgeMultiplier": str(surge_multiplier),
                "Helicone-Property-batch": "false",
                "Helicone-Property-ismarginBased": "false",
                "Helicone-Property-marginPercent": "0",
            }

            payload = {
                "providerRequest": {
                    "url": "custom-model-nopath",
                    "json": {
                        "model": f"mog/{service_id}",
                        "messages": [
                            {"role": "user", "content": str(params)},
                        ],
                        "_type": "tool",
                        "toolName": service_id,
                    },
                    "meta": {},
                },
                "providerResponse": {
                    "headers": {},
                    "status": 200 if success else 500,
                    "json": {
                        "model": f"mog/{service_id}",
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": str(result)[:2000],
                                },
                                "finish_reason": "stop" if success else "error",
                            }
                        ],
                        "usage": {
                            "prompt_tokens": credits_charged,
                            "completion_tokens": 0,
                            "total_tokens": credits_charged,
                        },
                        "_type": "tool",
                        "toolName": service_id,
                    },
                },
                "timing": {
                    "startTime": {
                        "seconds": int(start),
                        "milliseconds": int((start - int(start)) * 1000),
                    },
                    "endTime": {
                        "seconds": int(now),
                        "milliseconds": int((now - int(now)) * 1000),
                    },
                },
            }

            resp = httpx.post(HELICONE_LOGGING_URL, json=payload, headers=headers, timeout=5)
            if resp.status_code != 200:
                print(f"[helicone] log failed ({resp.status_code}): {resp.text[:200]}")
        except Exception as exc:
            print(f"[helicone] log error: {exc}")

    threading.Thread(target=_send, daemon=True).start()
