"""Scan the Nevermined marketplace: subscribe, test, and assess resell potential."""

import httpx, os, json, time, base64
from dotenv import load_dotenv
from payments_py import Payments, PaymentOptions

load_dotenv()

payments = Payments.get_instance(PaymentOptions(
    nvm_api_key=os.getenv("NVM_BUYER_API_KEY"),
    environment="sandbox",
))

# Get all sellers
resp = httpx.get(
    "https://nevermined.ai/hackathon/register/api/discover",
    params={"side": "sell"},
    headers={"x-nvm-api-key": os.getenv("NVM_API_KEY")},
    timeout=15,
)
sellers = resp.json().get("sellers", [])
print(f"Found {len(sellers)} sellers\n")

results = []

for i, s in enumerate(sellers):
    name = s.get("name", "unknown")
    team = s.get("teamName", "unknown")
    endpoint = s.get("endpointUrl", "")
    description = s.get("description", "")[:200]
    services_sold = s.get("servicesSold", "")[:200]
    category = s.get("category", "")
    plans = s.get("planPricing", [])

    print(f"[{i+1}/{len(sellers)}] {name} ({team})")
    print(f"  Endpoint: {endpoint}")
    print(f"  Plans: {len(plans)}")

    entry = {
        "name": name,
        "team": team,
        "endpoint": endpoint,
        "category": category,
        "description": description,
        "services_sold": services_sold,
        "plans": plans,
        "status": None,
        "subscribe_result": None,
        "test_status": None,
        "test_response": None,
        "auth_method": None,
        "server_type": None,
        "tools": None,
        "resell_assessment": None,
        "error": None,
    }

    # Skip if no endpoint or localhost
    if not endpoint or "localhost" in endpoint or endpoint.startswith("/"):
        entry["status"] = "skipped"
        entry["error"] = "no_valid_endpoint"
        print(f"  SKIP: no valid endpoint")
        results.append(entry)
        print()
        continue

    # Skip ourselves
    if "mog" in name.lower() and "market" in name.lower():
        entry["status"] = "skipped"
        entry["error"] = "self"
        print(f"  SKIP: that's us")
        results.append(entry)
        print()
        continue

    # Pick cheapest plan (prefer free, then cheapest USDC)
    chosen_plan = None
    for p in sorted(plans, key=lambda x: x.get("planPrice", 999)):
        chosen_plan = p
        break

    if not chosen_plan and plans:
        chosen_plan = plans[0]

    if not chosen_plan:
        # Try 402 probe to get plan ID
        try:
            probe = httpx.post(endpoint, headers={"Content-Type": "application/json"}, json={}, timeout=10)
            if probe.status_code == 402 and "payment-required" in probe.headers:
                payment_info = json.loads(base64.b64decode(probe.headers["payment-required"]))
                plan_id = payment_info["accepts"][0]["planId"]
                chosen_plan = {"planDid": plan_id, "planPrice": 0, "pricePerRequestFormatted": "unknown (from 402)"}
                print(f"  Got plan from 402 probe: {plan_id[:30]}...")
            else:
                entry["status"] = "skipped"
                entry["error"] = f"no_plan_id_probe_{probe.status_code}"
                print(f"  SKIP: no plan ID (probe returned {probe.status_code})")
                results.append(entry)
                print()
                continue
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = f"probe_error: {str(e)[:100]}"
            print(f"  FAIL: probe error: {str(e)[:80]}")
            results.append(entry)
            print()
            continue

    plan_id = chosen_plan.get("planDid", "")
    plan_price = chosen_plan.get("planPrice", 0)
    price_label = chosen_plan.get("pricePerRequestFormatted", f"{plan_price} USDC")

    print(f"  Plan: {price_label} (ID: {plan_id[:30]}...)")

    # Skip if too expensive (cap at 5 USDC per plan)
    if plan_price > 5:
        entry["status"] = "skipped"
        entry["error"] = f"price_exceeds_budget_{plan_price}"
        print(f"  SKIP: too expensive ({plan_price} USDC)")
        results.append(entry)
        print()
        continue

    # Subscribe
    try:
        payments.plans.order_plan(plan_id)
        entry["subscribe_result"] = "success"
        print(f"  Subscribed!")
    except Exception as e:
        err = str(e)
        if "already" in err.lower():
            entry["subscribe_result"] = "already_subscribed"
            print(f"  Already subscribed")
        elif "NotEnoughBalance" in err:
            entry["status"] = "failed"
            entry["subscribe_result"] = "insufficient_balance"
            entry["error"] = "not enough USDC"
            print(f"  FAIL: not enough USDC")
            results.append(entry)
            print()
            continue
        elif "429" in err:
            entry["status"] = "failed"
            entry["subscribe_result"] = "rate_limited"
            entry["error"] = "429 Infura"
            print(f"  FAIL: 429 rate limited")
            results.append(entry)
            print()
            continue
        else:
            entry["status"] = "failed"
            entry["subscribe_result"] = "error"
            entry["error"] = err[:200]
            print(f"  FAIL subscribe: {err[:100]}")
            results.append(entry)
            print()
            continue

    # Get token
    try:
        token = payments.x402.get_x402_access_token(plan_id)["accessToken"]
    except Exception as e:
        entry["status"] = "failed"
        entry["error"] = f"token_error: {str(e)[:100]}"
        print(f"  FAIL: couldn't get token")
        results.append(entry)
        print()
        continue

    # Test call — try payment-signature first, then bearer
    for auth_method, headers in [
        ("payment-signature", {"payment-signature": token, "Content-Type": "application/json"}),
        ("bearer", {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}),
    ]:
        try:
            # Try MCP tools/list first
            test_resp = httpx.post(endpoint, headers=headers, json={
                "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1,
            }, timeout=15)

            if test_resp.status_code == 200:
                entry["auth_method"] = auth_method
                entry["test_status"] = 200
                body = test_resp.text[:500]
                entry["test_response"] = body

                # Check if it's MCP
                try:
                    j = test_resp.json()
                    tools = j.get("result", {}).get("tools", [])
                    if tools:
                        entry["server_type"] = "mcp"
                        entry["tools"] = [t.get("name", "?") for t in tools]
                    else:
                        entry["server_type"] = "rest_api"
                except:
                    entry["server_type"] = "rest_api"

                print(f"  SUCCESS ({auth_method}): {test_resp.status_code}")
                break
            elif test_resp.status_code in (401, 402, 403):
                if auth_method == "bearer":
                    entry["test_status"] = test_resp.status_code
                    entry["auth_method"] = "none_worked"
                    entry["error"] = f"auth_rejected_{test_resp.status_code}"
                    print(f"  Auth rejected: {test_resp.status_code}")
                continue
            else:
                # Try a plain REST call
                rest_resp = httpx.post(endpoint, headers=headers, json={"query": "test"}, timeout=15)
                entry["test_status"] = rest_resp.status_code
                entry["auth_method"] = auth_method
                entry["test_response"] = rest_resp.text[:500]
                if rest_resp.status_code == 200:
                    entry["server_type"] = "rest_api"
                    print(f"  SUCCESS (REST, {auth_method}): {rest_resp.status_code}")
                else:
                    print(f"  Call returned {rest_resp.status_code}")
                break
        except httpx.TimeoutException:
            entry["test_status"] = "timeout"
            entry["error"] = "timeout"
            print(f"  TIMEOUT ({auth_method})")
            if auth_method == "bearer":
                break
            continue
        except Exception as e:
            entry["error"] = f"call_error: {str(e)[:100]}"
            print(f"  ERROR: {str(e)[:80]}")
            break

    # Determine status
    if entry["test_status"] == 200:
        entry["status"] = "connected"
    elif entry["test_status"] == "timeout":
        entry["status"] = "timeout"
    elif entry.get("status") is None:
        entry["status"] = "subscribed_call_failed"

    # Resell assessment
    if entry["status"] == "connected":
        cost = plan_price
        svc = (description + " " + services_sold).lower()

        has_unique_data = any(w in svc for w in [
            "analytics", "intelligence", "data", "research", "score",
            "monitor", "audit", "portfolio", "arbitrage", "resilience",
            "sentiment", "risk", "compliance", "forecast",
        ])
        has_ai = any(w in svc for w in ["ai", "llm", "gpt", "claude", "summariz", "generat"])
        is_search = any(w in svc for w in ["search", "scrape", "crawl", "extract"])
        is_commodity = any(w in svc for w in ["weather", "price", "convert", "calculator", "echo"])
        tools_list = entry.get("tools", [])

        if cost == 0:
            margin = "infinite (free upstream)"
        elif cost <= 1:
            margin = "high (<=1 USDC, resell at 2-5x)"
        elif cost <= 5:
            margin = "moderate (1-5 USDC, thin margin)"
        else:
            margin = "low (>5 USDC, hard to markup)"

        # Determine if we already cover this
        our_services = ["search", "summariz", "weather", "image", "geolocation", "hackathon"]
        overlaps_us = any(w in svc for w in our_services)

        if has_unique_data and not overlaps_us:
            verdict = "WRAP — unique data/analysis we don't have"
        elif has_unique_data and overlaps_us:
            verdict = "MAYBE — unique but overlaps our catalog"
        elif has_ai and not overlaps_us:
            verdict = "MAYBE — AI service, check differentiation"
        elif is_commodity:
            verdict = "SKIP — commodity, already covered"
        elif is_search and overlaps_us:
            verdict = "SKIP — we have exa_search"
        elif entry.get("server_type") == "mcp" and tools_list:
            verdict = "EVALUATE — MCP server with tools, test quality"
        else:
            verdict = "EVALUATE — need to test output quality"

        entry["resell_assessment"] = {
            "cost_per_call": price_label,
            "margin": margin,
            "verdict": verdict,
            "overlaps_us": overlaps_us,
            "rationale": f"Category: {category}. {description[:100]}",
        }
    else:
        entry["resell_assessment"] = {
            "verdict": "N/A — not connectable",
            "cost_per_call": price_label,
        }

    results.append(entry)
    print()
    time.sleep(1)

# Save results
output_path = "data/marketplace_scan_2.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

# Summary
connected = [r for r in results if r["status"] == "connected"]
failed = [r for r in results if r["status"] in ("failed", "subscribed_call_failed")]
skipped = [r for r in results if r["status"] == "skipped"]
timeout = [r for r in results if r["status"] == "timeout"]

print("=" * 60)
print(f"SCAN COMPLETE: {len(results)} targets")
print(f"  Connected: {len(connected)}")
print(f"  Failed: {len(failed)}")
print(f"  Skipped: {len(skipped)}")
print(f"  Timeout: {len(timeout)}")
print()

if connected:
    print("CONNECTED SERVICES + RESELL ASSESSMENT:")
    for r in connected:
        resell = r.get("resell_assessment", {})
        print(f"  {r['name']} ({r['team']})")
        print(f"    Type: {r.get('server_type', '?')}")
        if r.get("tools"):
            print(f"    Tools: {r['tools']}")
        print(f"    Cost: {resell.get('cost_per_call', '?')}")
        print(f"    Margin: {resell.get('margin', '?')}")
        print(f"    Verdict: {resell.get('verdict', '?')}")
        print()

# Resell summary
wrappable = [r for r in connected if "WRAP" in r.get("resell_assessment", {}).get("verdict", "")]
maybe = [r for r in connected if "MAYBE" in r.get("resell_assessment", {}).get("verdict", "") or "EVALUATE" in r.get("resell_assessment", {}).get("verdict", "")]
print(f"RESELL CANDIDATES:")
print(f"  WRAP (strong): {len(wrappable)} — {[r['name'] for r in wrappable]}")
print(f"  MAYBE/EVALUATE: {len(maybe)} — {[r['name'] for r in maybe]}")
print()

print(f"Results saved to {output_path}")
