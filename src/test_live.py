"""Smoke test: verify all Mog agents, plans, and services on the live gateway."""

import httpx
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from payments_py import Payments, PaymentOptions

payments = Payments.get_instance(PaymentOptions(
    nvm_api_key=os.getenv("NVM_DEBUGGER_BUYER_KEY") or os.getenv("NVM_API_KEY"),
    environment="sandbox",
))

EP = "https://api.mog.markets/mcp"
HEALTH = "https://api.mog.markets/health"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

PLANS = {
    "Mog Markets $1": "27532529988899010156793041100542920191141640561034683667962973311488756564499",
    "Mog Markets $5": "6476982684193144215967979389100088950230657664983966011439423784485034538208",
    "Mog Markets $10": "29001175520261924428527314088863841592234134735048963980654691130902766240562",
    "Mog Debugger $1": "100055324343248574008048211366287624670698094501751189055453802807316586516007",
}

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


# --- Health ---
print("Health check")
try:
    h = httpx.get(HEALTH, timeout=10)
    health = h.json()
    check("endpoint reachable", h.status_code == 200)
    check(f"services loaded ({health['services_count']})", health["services_count"] >= 15)
except Exception as e:
    check("endpoint reachable", False, str(e)[:100])
    print("\nGateway unreachable — aborting.")
    sys.exit(1)

# --- Subscribe + Token ---
print("\nSubscribe + token")
tokens = {}
for label, plan_id in PLANS.items():
    try:
        payments.plans.order_plan(plan_id)
        sub_ok = True
    except Exception as e:
        sub_ok = "already" in str(e).lower()
    check(f"{label} subscribe", sub_ok)

    try:
        token = payments.x402.get_x402_access_token(plan_id)["accessToken"]
        tokens[label] = token
        check(f"{label} token", True)
    except Exception as e:
        check(f"{label} token", False, str(e)[:80])

# --- tools/list ---
print("\ntools/list")
for label, token in tokens.items():
    hdrs = {**HEADERS, "Authorization": f"Bearer {token}"}
    r = httpx.post(EP, headers=hdrs, json={
        "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1,
    }, timeout=15)
    tools = r.json().get("result", {}).get("tools", []) if r.status_code == 200 else []
    check(f"{label} tools/list", r.status_code == 200 and len(tools) == 2,
          f"{r.status_code}, {len(tools)} tools")

# --- Functional tests ---
token = list(tokens.values())[0] if tokens else None
if not token:
    print("\nNo tokens — skipping functional tests.")
    sys.exit(1)

hdrs = {**HEADERS, "Authorization": f"Bearer {token}"}

print("\nfind_service")
r = httpx.post(EP, headers=hdrs, json={
    "jsonrpc": "2.0", "method": "tools/call",
    "params": {"name": "find_service", "arguments": {"query": "weather"}},
    "id": 10,
}, timeout=15)
if r.status_code == 200:
    text = r.json().get("result", {}).get("content", [{}])[0].get("text", "")
    results = json.loads(text)
    check("find_service", len(results) > 0, f"{len(results)} results")
else:
    check("find_service", False, f"status {r.status_code}")

print("\nbuy_and_call: weather")
r = httpx.post(EP, headers=hdrs, json={
    "jsonrpc": "2.0", "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "open_meteo_weather",
        "params": {"latitude": 37.77, "longitude": -122.42},
    }},
    "id": 11,
}, timeout=15)
if r.status_code == 200:
    text = r.json().get("result", {}).get("content", [{}])[0].get("text", "")
    outer = json.loads(text)
    credits = outer.get("_meta", {}).get("credits_charged")
    check("buy_and_call weather", credits == 1, f"credits_charged={credits}")
else:
    check("buy_and_call weather", False, f"status {r.status_code}")

print("\nbuy_and_call: debug_seller")
r = httpx.post(EP, headers=hdrs, json={
    "jsonrpc": "2.0", "method": "tools/call",
    "params": {"name": "buy_and_call", "arguments": {
        "service_id": "debug_seller",
        "params": {"team_name": "AIBizBrain"},
    }},
    "id": 12,
}, timeout=90)
if r.status_code == 200:
    text = r.json().get("result", {}).get("content", [{}])[0].get("text", "")
    outer = json.loads(text)
    result_str = outer.get("result", "{}")
    report = json.loads(result_str) if isinstance(result_str, str) else result_str
    verdict = report.get("verdict")
    credits = outer.get("_meta", {}).get("credits_charged")
    check("buy_and_call debug_seller", verdict == "PASS",
          f"verdict={verdict}, credits={credits}")
else:
    check("buy_and_call debug_seller", False, f"status {r.status_code}")

# --- Discovery API ---
print("\nDiscovery API listing")
resp = httpx.get(
    "https://nevermined.ai/hackathon/register/api/discover",
    params={"side": "sell"},
    headers={"x-nvm-api-key": os.getenv("NVM_API_KEY")},
    timeout=15,
)
sellers = resp.json().get("sellers", [])
ours = [s for s in sellers if "mog" in s.get("teamName", "").lower()]
check("Mog Markets listed", any("Mog Markets" in s["name"] for s in ours))
check("Mog Debugger listed", any("Debugger" in s["name"] for s in ours))

# --- Summary ---
print(f"\n{'=' * 40}")
if failures:
    print(f"FAILED: {len(failures)} checks")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
