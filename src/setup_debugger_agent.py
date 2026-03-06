"""Register Mog Debugger agent + plan on Nevermined.

Separate agent from Mog Markets. One plan: $1 USDC for 100 credits.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
RECEIVER = "0xca676aFBa6c12fb49Fd68Af9a1B400A577A3D58a"
GATEWAY_URL = "https://api.mog.markets"
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

if not NVM_API_KEY:
    print("Missing NVM_API_KEY in .env")
    sys.exit(1)

from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_erc20_price_config, get_dynamic_credits_config

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="Mog Debugger",
        description=(
            "Debug any Nevermined marketplace agent. We try to buy from them and "
            "return a full diagnostic report: pass/fail, discovery status, endpoint "
            "reachability, subscription flow, auth methods, known bugs, and actionable "
            "fixes. Call buy_and_call with service_id='debug_seller' and pass team_name."
        ),
        tags=["debugger", "diagnostics", "marketplace", "testing", "mcp"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[Endpoint(verb="POST", url=f"{GATEWAY_URL}/mcp")],
        agent_definition_url=f"{GATEWAY_URL}/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="Debug Credits",
        description="100 credits for $1 USDC. Each debug run costs 2 credits.",
    ),
    price_config=get_erc20_price_config(
        amount=1_000_000,  # 1 USDC in micro-USDC
        token_address=USDC_BASE_SEPOLIA,
        receiver=RECEIVER,
    ),
    credits_config=get_dynamic_credits_config(
        credits_granted=100,
        min_credits_per_request=1,
        max_credits_per_request=10,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]

print(f"Agent registered: {agent_id}")
print(f"Plan registered:  {plan_id}")

with open(".env", "a") as f:
    f.write(f"\n# Mog Debugger (separate agent, $1 USDC / 100 credits)\n")
    f.write(f"NVM_DEBUGGER_AGENT_ID={agent_id}\n")
    f.write(f"NVM_DEBUGGER_PLAN_ID={plan_id}\n")

print(f"\nNVM_DEBUGGER_AGENT_ID and NVM_DEBUGGER_PLAN_ID written to .env")
print("The debugger runs through the existing gateway — no separate server needed.")
