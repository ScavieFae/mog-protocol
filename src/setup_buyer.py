"""Register the Mog Buyer agent on Nevermined (Lynn Fairchild account)."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_BUYER_API_KEY = os.getenv("NVM_BUYER_API_KEY")

if not NVM_BUYER_API_KEY:
    print("Missing NVM_BUYER_API_KEY in .env")
    sys.exit(1)

from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_free_price_config, get_dynamic_credits_config

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_BUYER_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="Mog Buyer",
        description="Autonomous buyer agent for the Mog Marketplace. Discovers and purchases API services via find_service + buy_and_call. Evaluates ROI across search, summarization, and content extraction tools.",
        tags=["buyer", "marketplace", "autonomous", "mog"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url="mcp://mog-buyer/tools/find_service"),
            Endpoint(verb="POST", url="mcp://mog-buyer/tools/buy_and_call"),
        ],
        agent_definition_url="mcp://mog-buyer/tools/*",
    ),
    plan_metadata=PlanMetadata(
        name="Mog Buyer Credits",
        description="Operating budget for the Mog Buyer agent. Used to purchase services from the Mog Marketplace gateway.",
    ),
    price_config=get_free_price_config(),
    credits_config=get_dynamic_credits_config(
        credits_granted=100,
        min_credits_per_request=1,
        max_credits_per_request=10,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]

print(f"Buyer agent registered: {agent_id}")
print(f"Buyer plan registered:  {plan_id}")
print(f"\nNVM_BUYER_AGENT_ID={agent_id}")
print(f"NVM_BUYER_PLAN_ID={plan_id}")

# Append to .env
with open(".env", "a") as f:
    f.write(f"\nNVM_BUYER_AGENT_ID={agent_id}\n")
    f.write(f"NVM_BUYER_PLAN_ID={plan_id}\n")

print("\nWritten to .env. Check nevermined.app under Lynn's account — Mog Buyer should appear.")
