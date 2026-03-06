#!/usr/bin/env python3
"""One-command onboarding to the Mog Marketplace + Nevermined hackathon tools.

Run this and you get:
  - Subscription to the Mog Marketplace (free sponsored plan, 100 credits)
  - An MCP config ready to paste into Claude Code or any MCP-compatible agent
  - Access to 22 services: web search, content extraction, summarization,
    image generation, weather, math, QR codes, hackathon tools, and more

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

    PLAN_ID = "100055324343248574008048211366287624670698094501751189055453802807316586516007"
    GATEWAY = "https://api.mog.markets/mcp"

    print("Connecting to Nevermined sandbox...")
    payments = Payments.get_instance(
        PaymentOptions(nvm_api_key=api_key, environment="sandbox")
    )

    print("Subscribing to Mog Marketplace (free sponsored plan, 100 credits)...")
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
    print("22 services available:")
    print("  exa_search          (1 cr)  Semantic web search")
    print("  exa_get_contents    (2 cr)  Full text extraction from URLs")
    print("  claude_summarize    (5 cr)  AI summarization")
    print("  nano_banana_pro    (10 cr)  Image generation")
    print("  open_meteo_weather  (1 cr)  Weather forecast")
    print("  ip_geolocation      (1 cr)  IP location lookup")
    print("  frankfurter_fx_rates(1 cr)  FX rates")
    print("  hacker_news_top     (2 cr)  Top HN stories")
    print("  newton_math         (2 cr)  Symbolic math")
    print("  qr_code             (1 cr)  QR code generation")
    print("  hackathon_discover  (1 cr)  Find hackathon agents")
    print("  hackathon_portal    (1 cr)  Marketplace content")
    print("  hackathon_onboarding(1 cr)  Onboarding guide")
    print("  hackathon_pitfalls  (1 cr)  PaymentsMCP gotchas")
    print("  hackathon_all       (1 cr)  All hackathon context")
    print("  debug_seller        (1 cr)  Diagnose seller agents")
    print("  browser_navigate    (5 cr)  Headless browser")
    print("  agent_email_inbox   (1 cr)  Agent email")
    print("  social_search       (1 cr)  Social/Twitter search")
    print("  archive_fetch       (1 cr)  Wayback Machine")
    print("  circle_faucet       (1 cr)  USDC testnet faucet")
    print("  zeroclick_search    (1 cr)  ZeroClick search")
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
