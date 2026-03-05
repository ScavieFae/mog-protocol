"""Register the Mog Gateway marketplace agent on Nevermined."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")
GATEWAY_URL = os.getenv("MCP_SERVER_URL", "https://beneficial-essence-production-99c7.up.railway.app")

if not NVM_API_KEY:
    print("Missing NVM_API_KEY in .env")
    sys.exit(1)

from payments_py import Payments, PaymentOptions
from payments_py.common.types import AgentMetadata, AgentAPIAttributes, Endpoint, PlanMetadata
from payments_py.plans import get_free_price_config, get_dynamic_credits_config

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=NVM_API_KEY,
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

result = payments.agents.register_agent_and_plan(
    agent_metadata=AgentMetadata(
        name="Mog Markets Gateway",
        description="API marketplace with two-tool interface. find_service discovers APIs (search, summarize, weather, more). buy_and_call pays and executes in one step. ~200 tokens of context, any number of services. Dynamic pricing with surge.",
        tags=["marketplace", "gateway", "mcp", "search", "summarize", "mog"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url=f"{GATEWAY_URL}/mcp"),
        ],
        agent_definition_url=f"{GATEWAY_URL}/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="Mog Markets Access",
        description="Access to the Mog API marketplace. find_service is free. buy_and_call costs 1-10 credits depending on the service.",
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

print(f"Gateway agent registered: {agent_id}")
print(f"Gateway plan registered:  {plan_id}")
print(f"Gateway URL: {GATEWAY_URL}/mcp")
print(f"\nNVM_GATEWAY_AGENT_ID={agent_id}")
print(f"NVM_GATEWAY_PLAN_ID={plan_id}")

with open(".env", "a") as f:
    f.write(f"\nNVM_GATEWAY_AGENT_ID={agent_id}\n")
    f.write(f"NVM_GATEWAY_PLAN_ID={plan_id}\n")

print("\nWritten to .env.")
print(f"\nShare this with buyer teams:")
print(f"  Gateway: {GATEWAY_URL}/mcp")
print(f"  Plan ID: {plan_id}")
