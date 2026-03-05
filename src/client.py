"""Self-buy client — subscribe to plan, get token, call exa_search, verify credits burn."""

import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

NVM_SUBSCRIBER_API_KEY = os.getenv("NVM_SUBSCRIBER_API_KEY")
NVM_PLAN_ID = os.getenv("NVM_PLAN_ID")
SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000")

if not NVM_SUBSCRIBER_API_KEY:
    print("Missing NVM_SUBSCRIBER_API_KEY in .env — get a subscriber API key from https://nevermined.app")
    sys.exit(1)

if not NVM_PLAN_ID:
    print("Missing NVM_PLAN_ID in .env — run `python -m src.setup_agent` first")
    sys.exit(1)

from payments_py import Payments, PaymentOptions

subscriber = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_SUBSCRIBER_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

# Check balance / subscribe
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

# Call exa_search via JSON-RPC
print(f"\nCalling exa_search on {SERVER_URL}/mcp ...")
response = httpx.post(
    f"{SERVER_URL}/mcp",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    },
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "exa_search", "arguments": {"query": "Nevermined autonomous AI agents", "max_results": 3}},
        "id": 1,
    },
    timeout=30,
)

response.raise_for_status()
data = response.json()

if "error" in data:
    print(f"Error: {data['error']}")
    sys.exit(1)

result = data.get("result", {})
content = result.get("content", [])
meta = result.get("_meta", {})

print("\n=== Results ===")
if content:
    text = content[0].get("text", "")
    items = json.loads(text)
    for item in items:
        print(f"  {item['title']}")
        print(f"  {item['url']}")
        print()

print(f"=== Payment Meta ===")
print(json.dumps(meta, indent=2))
