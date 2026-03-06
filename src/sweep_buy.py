"""Sweep: subscribe to and test every reachable seller on the marketplace.

Runs with two keys (buyer + seller) to maximize leaderboard transactions.
Skips: our own agents, localhost endpoints, fiat-only plans.
"""

import base64
import httpx
import json
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

from payments_py import Payments, PaymentOptions

# --- Config ---
MAX_CRYPTO_PRICE = 15  # Skip plans above this USDC
SKIP_TEAMS = {"mog markets"}
TIMEOUT = 30

KEYS = {
    "buyer": os.getenv("NVM_DEBUGGER_BUYER_KEY"),
    "seller": os.getenv("NVM_API_KEY"),
}

# --- Discovery ---
def discover_sellers():
    resp = httpx.get(
        "https://nevermined.ai/hackathon/register/api/discover",
        params={"side": "sell"},
        headers={"x-nvm-api-key": os.getenv("NVM_API_KEY")},
        timeout=15,
    )
    return resp.json().get("sellers", [])


def is_reachable_endpoint(ep):
    if not ep:
        return False
    ep = ep.strip()
    if ep.startswith("/") or ep.startswith("http://localhost") or ep.startswith("http://127."):
        return False
    if ep.startswith("http://seller:"):
        return False
    if not ep.startswith("http"):
        return False
    return True


def get_crypto_plans(seller):
    plans = []
    for p in seller.get("planPricing", []):
        if p.get("paymentType") == "crypto":
            price = float(p.get("planPrice", 999))
            if price <= MAX_CRYPTO_PRICE:
                plans.append({
                    "plan_id": p["planDid"],
                    "price": price,
                    "type": "crypto",
                })
    plans.sort(key=lambda x: x["price"])
    return plans


# --- Test an endpoint ---
def test_endpoint(endpoint, token):
    """Try MCP tools/list, then a tool call. Return results dict."""
    results = {"tools_list": None, "tool_calls": [], "type": "unknown"}

    # Try Bearer auth first, then payment-signature
    for auth_style in ["bearer", "payment-signature"]:
        if auth_style == "bearer":
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
        else:
            headers = {
                "payment-signature": token,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }

        try:
            r = httpx.post(endpoint, headers=headers, json={
                "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1,
            }, timeout=TIMEOUT)
        except Exception as e:
            results["tools_list"] = {"error": str(e)[:150], "auth": auth_style}
            continue

        if r.status_code == 200:
            try:
                body = r.json()
            except Exception:
                results["tools_list"] = {"status": 200, "body": r.text[:300], "auth": auth_style, "error": "non-JSON response"}
                return results
            tools = body.get("result", {}).get("tools", [])
            if tools:
                results["type"] = "mcp"
                results["auth"] = auth_style
                results["tools_list"] = {
                    "status": 200,
                    "tool_count": len(tools),
                    "tools": [t.get("name", "?")[:50] for t in tools],
                    "auth": auth_style,
                }
                # Try calling each tool
                for t in tools:
                    name = t.get("name", "")
                    try:
                        cr = httpx.post(endpoint, headers=headers, json={
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {"name": name, "arguments": {}},
                            "id": 100,
                        }, timeout=TIMEOUT)
                        resp_text = cr.text[:300]
                        results["tool_calls"].append({
                            "tool": name,
                            "status": cr.status_code,
                            "response": resp_text,
                        })
                    except Exception as e:
                        results["tool_calls"].append({
                            "tool": name,
                            "status": "error",
                            "response": str(e)[:150],
                        })
                return results
            else:
                # 200 but no tools — might be REST
                results["type"] = "rest_or_mcp_no_tools"
                results["tools_list"] = {
                    "status": 200,
                    "body": r.text[:300],
                    "auth": auth_style,
                }
                return results

        elif r.status_code in (401, 402, 403):
            results["tools_list"] = {
                "status": r.status_code,
                "auth": auth_style,
                "body": r.text[:200],
            }
            continue  # try other auth style
        else:
            results["tools_list"] = {
                "status": r.status_code,
                "body": r.text[:200],
                "auth": auth_style,
            }
            # For REST endpoints, try a simple POST
            if r.status_code != 404:
                return results

    # If MCP failed, try as REST
    for auth_style in ["bearer", "payment-signature"]:
        if auth_style == "bearer":
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "payment-signature": token,
                "Content-Type": "application/json",
            }
        try:
            r = httpx.post(endpoint, headers=headers, json={"query": "test"}, timeout=TIMEOUT)
            results["type"] = "rest"
            results["auth"] = auth_style
            results["rest_response"] = {
                "status": r.status_code,
                "body": r.text[:300],
            }
            if r.status_code == 200:
                return results
        except httpx.ConnectError as e:
            results["rest_response"] = {"error": f"connect: {str(e)[:100]}"}
        except httpx.ReadTimeout:
            results["rest_response"] = {"error": "timeout"}
        except Exception as e:
            results["rest_response"] = {"error": str(e)[:150]}
    return results


# --- Main sweep ---
def run_sweep():
    sellers = discover_sellers()
    print(f"Discovered {len(sellers)} sellers\n")

    # Filter viable targets
    targets = []
    for s in sellers:
        team = s.get("teamName", "").lower()
        if team in SKIP_TEAMS:
            continue
        ep = s.get("endpointUrl", "")
        if not is_reachable_endpoint(ep):
            continue
        plans = get_crypto_plans(s)
        if not plans:
            continue
        targets.append({
            "team": s.get("teamName", "?"),
            "name": s.get("name", "?"),
            "endpoint": ep,
            "plans": plans,
        })

    print(f"Viable targets (reachable + crypto plans): {len(targets)}\n")
    for t in targets:
        plan_strs = [f"${p['price']}" for p in t["plans"]]
        print(f"  {t['team']:30s} | {t['name'][:45]:45s} | plans: {', '.join(plan_strs)}")
    print()

    all_results = []

    for key_label, api_key in KEYS.items():
        if not api_key:
            print(f"\n[SKIP] {key_label} key not set\n")
            continue

        print(f"\n{'='*60}")
        print(f"KEY: {key_label}")
        print(f"{'='*60}\n")

        payments = Payments.get_instance(PaymentOptions(
            nvm_api_key=api_key,
            environment="sandbox",
        ))

        for target in targets:
            for plan in target["plans"]:
                plan_id = plan["plan_id"]
                label = f"{target['team']} / {target['name']} (${plan['price']})"
                print(f"--- {label} ---")

                # Subscribe
                try:
                    payments.plans.order_plan(plan_id)
                    sub_status = "subscribed"
                except Exception as e:
                    err = str(e).lower()
                    if "already" in err:
                        sub_status = "already_subscribed"
                    else:
                        sub_status = f"error: {str(e)[:100]}"
                print(f"  Subscribe: {sub_status}")

                # Token
                try:
                    token = payments.x402.get_x402_access_token(plan_id)["accessToken"]
                    token_ok = True
                except Exception as e:
                    token_ok = False
                    print(f"  Token: FAIL — {str(e)[:100]}")

                if not token_ok:
                    all_results.append({
                        "key": key_label, "team": target["team"],
                        "name": target["name"], "plan_price": plan["price"],
                        "subscribe": sub_status, "token": False,
                        "test": None,
                    })
                    print()
                    continue

                print(f"  Token: OK")

                # Test endpoint
                test = test_endpoint(target["endpoint"], token)
                tl = test.get("tools_list") or {}
                tc = test.get("tool_calls", [])

                if test["type"] == "mcp" and isinstance(tl, dict):
                    tools = tl.get("tools", [])
                    print(f"  Type: MCP | Tools: {tools}")
                    for c in tc:
                        status_str = c.get("status", "?")
                        resp_preview = c.get("response", "")[:120]
                        print(f"    Call {c['tool']}: {status_str} — {resp_preview}")
                else:
                    print(f"  Type: {test['type']} | {json.dumps(tl, default=str)[:200]}")

                all_results.append({
                    "key": key_label, "team": target["team"],
                    "name": target["name"], "plan_price": plan["price"],
                    "subscribe": sub_status, "token": True,
                    "test": test,
                })
                print()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")

    for key_label in KEYS:
        key_results = [r for r in all_results if r["key"] == key_label]
        subscribed = sum(1 for r in key_results if "subscri" in str(r["subscribe"]))
        tokens = sum(1 for r in key_results if r["token"])
        mcp_ok = sum(1 for r in key_results if r.get("test", {}) and r["test"].get("type") == "mcp")
        tool_calls = sum(len(r["test"].get("tool_calls", [])) for r in key_results if r.get("test"))
        print(f"{key_label}: {len(key_results)} plans tried, {subscribed} subscribed, {tokens} tokens, {mcp_ok} MCP servers, {tool_calls} tool calls")

    # Save results
    os.makedirs("data", exist_ok=True)
    with open("data/sweep_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nDetailed results saved to data/sweep_results.json")


if __name__ == "__main__":
    run_sweep()
