"""Register paid plans for Mog Markets.

Gateway — 3 tiers, each offered as both Card (fiat) and USDC (crypto):
  $1  / 1 USDC  →  1 credit   (1 API call)
  $5  / 5 USDC  → 10 credits
  $10 / 10 USDC → 20 credits

Hackathon Guide — $0.10 / 0.10 USDC per credit (1 credit per call)

Total: 8 plan registrations (4 tiers × 2 payment methods).
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
RECEIVER = "0xca676aFBa6c12fb49Fd68Af9a1B400A577A3D58a"  # Mattie's wallet
GATEWAY_URL = os.getenv("MCP_SERVER_URL", "https://beneficial-essence-production-99c7.up.railway.app")
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

if not NVM_API_KEY:
    print("Missing NVM_API_KEY in .env")
    sys.exit(1)

from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import (
    get_fiat_price_config,
    get_erc20_price_config,
    get_dynamic_credits_config,
)

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

# ---------------------------------------------------------------------------
# Gateway plans
# ---------------------------------------------------------------------------

GATEWAY_AGENT_META = AgentMetadata(
    name="Mog Markets",
    description=(
        "API marketplace for agents. Two tools: find_service (free discovery) "
        "and buy_and_call (pay per use). 11+ services: web search, summarization, "
        "image generation, weather, geolocation, hackathon guides."
    ),
    tags=["marketplace", "mcp", "search", "api", "gateway"],
)

GATEWAY_API = AgentAPIAttributes(
    endpoints=[Endpoint(verb="POST", url=f"{GATEWAY_URL}/mcp")],
    agent_definition_url=f"{GATEWAY_URL}/mcp",
)

GATEWAY_TIERS = [
    # (name_suffix, fiat_cents, usdc_units, credits_granted, min_cr, max_cr)
    ("1 credit",   100,  1_000_000,   1,  1,  1),
    ("10 credits",  500,  5_000_000,  10,  1, 10),
    ("20 credits", 1000, 10_000_000,  20,  1, 10),
]

# ---------------------------------------------------------------------------
# Hackathon Guide plans
# ---------------------------------------------------------------------------

GUIDE_AGENT_META = AgentMetadata(
    name="Nevermined Hackathon Guide",
    description=(
        "Can't read the hackathon portal? This MCP returns ingested website content, "
        "onboarding docs, and PaymentsMCP gotchas. 4 services, 1 credit each."
    ),
    tags=["hackathon", "onboarding", "guide", "nevermined", "documentation", "mcp"],
)

GUIDE_API = AgentAPIAttributes(
    endpoints=[Endpoint(verb="POST", url=f"{GATEWAY_URL}/mcp")],
    agent_definition_url=f"{GATEWAY_URL}/mcp",
)

GUIDE_TIERS = [
    # (name_suffix, fiat_cents, usdc_units, credits_granted, min_cr, max_cr)
    ("1 credit", 10, 100_000, 1, 1, 1),
]

# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

results = []


def register_pair(label, agent_meta, agent_api, tier):
    """Register one fiat + one crypto plan for a tier."""
    name_suffix, fiat_cents, usdc_units, credits, min_cr, max_cr = tier
    credits_config = get_dynamic_credits_config(
        credits_granted=credits,
        min_credits_per_request=min_cr,
        max_credits_per_request=max_cr,
    )

    fiat_price = fiat_cents / 100
    usdc_price = usdc_units / 1_000_000

    for method, price_config, price_label in [
        ("card", get_fiat_price_config(amount=fiat_cents, receiver=RECEIVER), f"${fiat_price:.2f}"),
        ("usdc", get_erc20_price_config(amount=usdc_units, token_address=USDC_BASE_SEPOLIA, receiver=RECEIVER), f"{usdc_price:.2f} USDC"),
    ]:
        plan_name = f"{label} — {method.upper()} {name_suffix} ({price_label})"
        print(f"  Registering: {plan_name} ...")
        try:
            result = payments.agents.register_agent_and_plan(
                agent_metadata=agent_meta,
                agent_api=agent_api,
                plan_metadata=PlanMetadata(
                    name=plan_name,
                    description=f"{credits} credit{'s' if credits > 1 else ''} for {price_label} via {method}. 1 credit = 1 API call.",
                ),
                price_config=price_config,
                credits_config=credits_config,
                access_limit="credits",
            )
            agent_id = result["agentId"]
            plan_id = result["planId"]
            print(f"    agent={agent_id}")
            print(f"    plan={plan_id}")
            results.append((label, method, name_suffix, agent_id, plan_id))
        except Exception as e:
            print(f"    FAILED: {e}")


# ---------------------------------------------------------------------------
# Run registrations
# ---------------------------------------------------------------------------

print("=== GATEWAY PLANS ===\n")
for tier in GATEWAY_TIERS:
    register_pair("Mog Markets", GATEWAY_AGENT_META, GATEWAY_API, tier)
    print()

print("=== HACKATHON GUIDE PLANS ===\n")
for tier in GUIDE_TIERS:
    register_pair("Hackathon Guide", GUIDE_AGENT_META, GUIDE_API, tier)
    print()

# ---------------------------------------------------------------------------
# Summary + save
# ---------------------------------------------------------------------------

print("=== RESULTS ===\n")
with open(".env", "a") as f:
    f.write("\n# --- Paid plans (registered by setup_paid_plans.py) ---\n")
    for label, method, tier_name, agent_id, plan_id in results:
        env_key = f"NVM_{label.upper().replace(' ', '_')}_{method.upper()}_{tier_name.upper().replace(' ', '_')}"
        print(f"{env_key}_PLAN_ID={plan_id}")
        f.write(f"{env_key}_AGENT_ID={agent_id}\n")
        f.write(f"{env_key}_PLAN_ID={plan_id}\n")

print(f"\n{len(results)} plans registered. IDs written to .env")
print("\nStripe test card: 4242 4242 4242 4242 (any future expiry, any CVC)")
print(f"Free plan still active: {os.getenv('NVM_GATEWAY_PLAN_ID')}")
