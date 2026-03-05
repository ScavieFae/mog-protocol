"""End-to-end vertical slice test: find_service → buy_and_call through the gateway.

Requires gateway running on GATEWAY_URL and NVM keys in .env.
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_SUBSCRIBER_API_KEY = os.getenv("NVM_SUBSCRIBER_API_KEY")
NVM_PLAN_ID = os.getenv("NVM_PLAN_ID")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:4000")

if not NVM_SUBSCRIBER_API_KEY or not NVM_PLAN_ID:
    print("Missing NVM_SUBSCRIBER_API_KEY or NVM_PLAN_ID in .env")
    sys.exit(1)

import httpx
from payments_py import Payments, PaymentOptions

subscriber = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_SUBSCRIBER_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

# Subscribe if needed
balance = subscriber.plans.get_plan_balance(NVM_PLAN_ID)
print(f"Plan balance: {balance}")

if not balance.is_subscriber:
    print("Not subscribed — ordering plan...")
    subscriber.plans.order_plan(NVM_PLAN_ID)
    print("Subscribed.")

# Get x402 access token
token_result = subscriber.x402.get_x402_access_token(NVM_PLAN_ID)
access_token = token_result["accessToken"]
print(f"Got access token: {access_token[:20]}...")


def gateway_call(method: str, name: str, arguments: dict) -> dict:
    """Make a JSON-RPC tool call to the gateway."""
    response = httpx.post(
        f"{GATEWAY_URL}/mcp",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "method": method,
            "params": {"name": name, "arguments": arguments},
            "id": 1,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# Step 1: find_service
print("\n=== Step 1: find_service('web search') ===")
resp = gateway_call("tools/call", "find_service", {"query": "web search"})

if "error" in resp:
    print(f"ERROR: {resp['error']}")
    sys.exit(1)

content = resp.get("result", {}).get("content", [])
if not content:
    print("No content in response")
    sys.exit(1)

services = json.loads(content[0].get("text", "[]"))
print(f"Found {len(services)} services:")
for svc in services:
    print(f"  {svc['service_id']}: {svc['name']} ({svc['price']} credits)")

# Step 2: buy_and_call with exa_search
target = services[0]
print(f"\n=== Step 2: buy_and_call('{target['service_id']}') ===")
resp2 = gateway_call("tools/call", "buy_and_call", {
    "service_id": target["service_id"],
    "params": {"query": "Nevermined AI agent marketplace", "max_results": 2},
})

if "error" in resp2:
    print(f"ERROR: {resp2['error']}")
    sys.exit(1)

content2 = resp2.get("result", {}).get("content", [])
if not content2:
    print("No content in response")
    sys.exit(1)

result_data = json.loads(content2[0].get("text", "{}"))
print(f"\nResult keys: {list(result_data.keys())}")

if "result" in result_data:
    items = json.loads(result_data["result"]) if isinstance(result_data["result"], str) else result_data["result"]
    if isinstance(items, list):
        for item in items:
            print(f"  {item.get('title', 'N/A')}")
            print(f"  {item.get('url', 'N/A')}")
            print()

meta = result_data.get("_meta", {})
print(f"=== Payment Meta ===")
print(f"  credits_charged: {meta.get('credits_charged')}")
print(f"  service_id: {meta.get('service_id')}")
print("\nEnd-to-end vertical slice COMPLETE.")
