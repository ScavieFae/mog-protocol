"""Transaction pump — generates real Nevermined transactions through the gateway.

Usage:
    python -m src.pump                        # single round, default account
    python -m src.pump --buyer                # use buyer account (Lynn)
    python -m src.pump --buyer --loop 0 --delay 30  # infinite buyer loop
    python -m src.pump --loop 10              # 10 rounds
"""

import argparse
import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

# Parse args early so we can pick the right key
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--buyer", action="store_true")
_early_args, _ = _parser.parse_known_args()

if _early_args.buyer:
    NVM_API_KEY = os.getenv("NVM_BUYER_API_KEY")
    AGENT_LABEL = "Mog Buyer (Lynn)"
else:
    NVM_API_KEY = os.getenv("NVM_SUBSCRIBER_API_KEY") or os.getenv("NVM_API_KEY")
    AGENT_LABEL = "Mog Seller (self-buy)"

NVM_PLAN_ID = os.getenv("NVM_PLAN_ID")
GATEWAY_URL = os.getenv("MCP_SERVER_URL", "https://beneficial-essence-production-99c7.up.railway.app")

if not NVM_API_KEY or not NVM_PLAN_ID:
    print("Missing API key or NVM_PLAN_ID in .env")
    if _early_args.buyer:
        print("For --buyer mode, set NVM_BUYER_API_KEY")
    sys.exit(1)

from payments_py import Payments, PaymentOptions

subscriber = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)


def get_token():
    """Get x402 access token for the gateway."""
    result = subscriber.x402.get_x402_access_token(NVM_PLAN_ID)
    return result["accessToken"]


def mcp_call(token: str, tool: str, arguments: dict) -> dict:
    """Make a JSON-RPC tools/call to the gateway."""
    resp = httpx.post(
        f"{GATEWAY_URL}/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
            "id": 1,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def run_round(token: str, round_num: int) -> dict:
    """One full transaction round: find_service -> buy_and_call."""
    queries = [
        "web search",
        "summarize text",
        "fetch web page content",
        "AI search engine",
        "content extraction from URLs",
    ]
    query = queries[round_num % len(queries)]

    # Step 1: find_service (free)
    print(f"  [{round_num}] find_service('{query}')...", end=" ")
    find_result = mcp_call(token, "find_service", {"query": query})
    content = find_result.get("result", {}).get("content", [])
    text = content[0].get("text", "[]") if content else "[]"
    services = json.loads(text)
    print(f"found {len(services)} services")

    if not services:
        print(f"  [{round_num}] No services found, skipping buy")
        return {"round": round_num, "query": query, "found": 0, "bought": None}

    # Step 2: buy_and_call (costs credits)
    target = services[0]
    service_id = target["service_id"]
    params = target.get("example_params", {})
    print(f"  [{round_num}] buy_and_call('{service_id}')...", end=" ")

    buy_result = mcp_call(token, "buy_and_call", {
        "service_id": service_id,
        "params": params,
    })
    buy_content = buy_result.get("result", {}).get("content", [])
    buy_text = buy_content[0].get("text", "{}") if buy_content else "{}"
    buy_data = json.loads(buy_text)
    meta = buy_data.get("_meta", {})
    credits = meta.get("credits_charged", "?")
    print(f"OK, {credits} credits")

    return {
        "round": round_num,
        "query": query,
        "found": len(services),
        "bought": service_id,
        "credits": credits,
    }


def main():
    parser = argparse.ArgumentParser(description="Transaction pump for Mog Gateway")
    parser.add_argument("--loop", type=int, default=1, help="Number of rounds (0=infinite)")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between rounds")
    parser.add_argument("--buyer", action="store_true", help="Use buyer account (Lynn)")
    args = parser.parse_args()

    # Check balance — subscribe first if needed
    print(f"Agent: {AGENT_LABEL}")
    balance = subscriber.plans.get_plan_balance(NVM_PLAN_ID)
    if not balance.is_subscriber:
        print("Not subscribed — ordering plan...")
        subscriber.plans.order_plan(NVM_PLAN_ID)
        balance = subscriber.plans.get_plan_balance(NVM_PLAN_ID)
        print("Subscribed!")
    print(f"Plan: {balance.plan_name}")
    print(f"Balance: {balance.balance} credits")
    print(f"Gateway: {GATEWAY_URL}")
    print()

    # Get token once (reusable across calls)
    print("Getting x402 access token...")
    token = get_token()
    print(f"Token: {token[:20]}...\n")

    total_tx = 0
    total_credits = 0
    round_num = 0

    try:
        while args.loop == 0 or round_num < args.loop:
            try:
                result = run_round(token, round_num)
                total_tx += 1
                if result.get("credits"):
                    total_credits += result["credits"] if isinstance(result["credits"], int) else 0
            except Exception as e:
                print(f"  [{round_num}] Error: {e}")
                # Get fresh token in case the old one expired
                token = get_token()

            round_num += 1
            if args.loop == 0 or round_num < args.loop:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\n\nStopped.")

    print(f"\n{'='*40}")
    print(f"Rounds: {total_tx}")
    print(f"Credits spent: {total_credits}")
    print(f"Gateway: {GATEWAY_URL}")


if __name__ == "__main__":
    main()
