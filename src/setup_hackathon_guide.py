"""Register the Nevermined Hackathon Guide agent on the marketplace.

This is a dedicated listing separate from the Mog Markets Gateway.
Targets hackers who need onboarding help — first transaction, gotchas,
deployment, PaymentsMCP setup. Points to our gateway, serves hackathon_guide.
"""

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
        name="Nevermined Hackathon Guide",
        description=(
            "Stuck on your first Nevermined transaction? This MCP returns "
            "curated onboarding docs: quickstart walkthrough, API key setup, "
            "PaymentsMCP gotchas, deployment to Railway, transaction flow, "
            "agent discovery, and MCP client config. "
            "8 topics, 1 credit each. Written from the hackathon floor "
            "by a team that hit every wall so you don't have to."
        ),
        tags=["hackathon", "onboarding", "guide", "nevermined", "documentation", "mcp"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url=f"{GATEWAY_URL}/mcp"),
        ],
        agent_definition_url=f"{GATEWAY_URL}/mcp",
    ),
    plan_metadata=PlanMetadata(
        name="Hackathon Guide Access",
        description=(
            "Access to Nevermined hackathon onboarding docs via MCP. "
            "Use buy_and_call('hackathon_guide', {'topic': 'quickstart'}) "
            "to get started. Topics: quickstart, api_key, transaction_flow, "
            "building_seller, deployment, discovery, gotchas, mcp_client."
        ),
    ),
    price_config=get_free_price_config(),
    credits_config=get_dynamic_credits_config(
        credits_granted=100,
        min_credits_per_request=1,
        max_credits_per_request=1,
    ),
    access_limit="credits",
)

agent_id = result["agentId"]
plan_id = result["planId"]

print(f"Hackathon Guide agent registered: {agent_id}")
print(f"Hackathon Guide plan registered:  {plan_id}")
print(f"Gateway URL: {GATEWAY_URL}/mcp")

with open(".env", "a") as f:
    f.write(f"\nNVM_GUIDE_AGENT_ID={agent_id}\n")
    f.write(f"NVM_GUIDE_PLAN_ID={plan_id}\n")

print("\nWritten to .env.")
print(f"\n--- PORTAL REGISTRATION (fill form at nevermined.ai/hackathon/register) ---")
print(f"  Name:        Nevermined Hackathon Guide")
print(f"  Team:        Mog Markets")
print(f"  Category:    Infrastructure")
print(f"  Description: Stuck on your first transaction? MCP that returns curated onboarding docs — quickstart, gotchas, deployment, PaymentsMCP setup. 8 topics, 1 credit each.")
print(f"  Endpoint:    {GATEWAY_URL}/mcp")
print(f"  Price:       1 credit/request")
print(f"  Agent ID:    {agent_id}")
print(f"  Plan ID:     {plan_id}")
