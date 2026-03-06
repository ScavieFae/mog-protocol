#!/usr/bin/env python3
"""One-command onboarding to the Mog Marketplace + Nevermined hackathon tools.

Run this and you get:
  - Subscription to the Mog Marketplace (free, 100 credits)
  - An MCP config ready to paste into Claude Code or any MCP-compatible agent
  - Access to 6 services: web search, content extraction, summarization,
    weather, hackathon agent discovery, and Nevermined onboarding docs

Usage:
    pip install payments-py httpx
    python onboard.py YOUR_NVM_API_KEY

Or set NVM_API_KEY in your environment:
    export NVM_API_KEY="sandbox:eyJ..."
    python onboard.py
"""

import json
import os
import sys

def main():
    # Get API key from arg or env
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("NVM_API_KEY")

    if not api_key:
        print("Usage: python onboard.py YOUR_NVM_API_KEY")
        print("  Or: export NVM_API_KEY='sandbox:eyJ...' && python onboard.py")
        print()
        print("Get your key at https://nevermined.app")
        print("  -> Create account -> Generate API key -> Enable ALL 4 permissions")
        sys.exit(1)

    try:
        from payments_py import Payments, PaymentOptions
    except ImportError:
        print("Missing payments-py. Install it:")
        print("  pip install payments-py httpx")
        sys.exit(1)

    PLAN_ID = "9661082042009636068072391467054896427087238025772062250717418964278633341785"
    GATEWAY = "https://beneficial-essence-production-99c7.up.railway.app/mcp"

    print("Connecting to Nevermined sandbox...")
    payments = Payments.get_instance(
        PaymentOptions(nvm_api_key=api_key, environment="sandbox")
    )

    print("Subscribing to Mog Marketplace (free, 100 credits)...")
    try:
        payments.plans.order_plan(PLAN_ID)
        print("  Subscribed.")
    except Exception as e:
        if "already" in str(e).lower():
            print("  Already subscribed.")
        else:
            print(f"  Subscribe returned: {e}")
            print("  (Continuing — you may already be subscribed)")

    print("Getting x402 access token...")
    token = payments.x402.get_x402_access_token(PLAN_ID)["accessToken"]
    print(f"  Token: {token[:40]}...")

    # Build MCP config
    mcp_config = {
        "mcpServers": {
            "mog-marketplace": {
                "type": "http",
                "url": GATEWAY,
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    }

    print()
    print("=" * 60)
    print("  MOG MARKETPLACE - READY")
    print("=" * 60)
    print()
    print("Add this to your .mcp.json or MCP config:")
    print()
    print(json.dumps(mcp_config, indent=2))
    print()
    print("Your agent gets two tools:")
    print("  find_service  - search the marketplace (free)")
    print("  buy_and_call  - pay and execute a service")
    print()
    print("Services available:")
    print("  exa_search        (1 cr)  Web search with snippets + URLs")
    print("  exa_get_contents  (2 cr)  Full text extraction from URLs")
    print("  claude_summarize  (5 cr)  AI summarization")
    print("  open_meteo_weather(1 cr)  Weather forecast")
    print("  hackathon_discover(1 cr)  Find agents on the hackathon portal")
    print("  hackathon_guide   (1 cr)  Nevermined onboarding docs & gotchas")
    print()
    print("Quick test:")
    print(f'  curl -X POST {GATEWAY} \\')
    print(f'    -H "Authorization: Bearer {token[:30]}..." \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"jsonrpc":"2.0","id":1,"method":"tools/call",')
    print(f'         "params":{{"name":"find_service","arguments":{{"query":"search"}}}}}}\'')
    print()

    # Also write config to file for convenience
    config_path = ".mcp-mog.json"
    with open(config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)
    print(f"Config also saved to {config_path}")
    print("  Merge it into your .mcp.json to connect your agent.")


if __name__ == "__main__":
    main()
