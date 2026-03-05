"""Register Exa search agent + plan with Nevermined."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NVM_API_KEY = os.getenv("NVM_API_KEY")

if not NVM_API_KEY:
    print("Missing NVM_API_KEY in .env — get a builder API key from https://nevermined.app")
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
        name="Mog Exa Search",
        description="Semantic web search via Exa. Fast, relevant results with source URLs and full text extraction.",
        tags=["search", "exa", "mcp", "web"],
    ),
    agent_api=AgentAPIAttributes(
        endpoints=[
            Endpoint(verb="POST", url="mcp://mog-exa/tools/exa_search"),
            Endpoint(verb="POST", url="mcp://mog-exa/tools/exa_get_contents"),
        ],
        agent_definition_url="mcp://mog-exa/tools/*",
    ),
    plan_metadata=PlanMetadata(
        name="Mog Exa Credits",
        description="Credits for Exa search and content fetching. exa_search=1 credit, exa_get_contents=2 credits.",
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

print(f"Agent registered: {agent_id}")
print(f"Plan registered:  {plan_id}")

# Append to .env
env_path = ".env"
with open(env_path, "a") as f:
    f.write(f"\nNVM_AGENT_ID={agent_id}\n")
    f.write(f"NVM_PLAN_ID={plan_id}\n")

print(f"\nNVM_AGENT_ID and NVM_PLAN_ID written to {env_path}")
print("Next: start the server with `python -m src.server`")
