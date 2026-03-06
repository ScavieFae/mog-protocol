# x402 Fiat (Card Delegation) Flow

Source: https://github.com/nevermined-io/hackathons/blob/main/workshops/x402/slides.md
Reference client: https://github.com/nevermined-io/hackathons/blob/main/workshops/x402/demo/src/client.py

## How Fiat Works

Card delegation = "pre-authorized tab at a bar"

1. Buyer enrolls card at nevermined.app (one-time)
2. Buyer requests token with `CardDelegationConfig` (payment method ID, spending limit, duration)
3. Nevermined validates card via Stripe API, creates delegation, signs JWT
4. On each request settlement:
   - Credits available? → Burn them (same as crypto)
   - Credits exhausted? → Charge card → Mint credits on-chain → Burn

## Buyer Code (Python)

```python
from payments_py.x402.resolve_scheme import resolve_scheme
from payments_py.x402.types import CardDelegationConfig, X402TokenOptions

scheme = resolve_scheme(payments, plan_id)  # "nvm:card-delegation" for fiat

if scheme == "nvm:card-delegation":
    methods = payments.delegation.list_payment_methods()
    token_options = X402TokenOptions(
        scheme=scheme,
        delegation_config=CardDelegationConfig(
            provider_payment_method_id=methods[0].id,
            spending_limit_cents=10_000,  # $100
            duration_secs=604_800,        # 7 days
            currency="usd",
        ),
    )
else:
    token_options = X402TokenOptions(scheme=scheme)  # crypto

token = payments.x402.get_x402_access_token(plan_id, token_options=token_options)
```

## Seller Code

Seller code is identical for crypto and fiat. `PaymentMiddleware` or `PaymentsMCP` handles both automatically based on plan metadata.

## Key Facts

- `resolve_scheme()` auto-detects crypto vs fiat from plan's `isCrypto` field
- Fiat plans: `isCrypto: false`, scheme `nvm:card-delegation`, network `stripe`
- Crypto plans: `isCrypto: true`, scheme `nvm:erc4337`, network `eip155:84532`
- Credits are always ERC-1155 on-chain, even for fiat (minted on card charge)
- Seller never touches buyer's wallet or card — Nevermined facilitates
- Two plans on same agent = both payment types, zero code changes on seller

## Confirmed Working (Mog Protocol, 2026-03-06)

- Bought from AgentAudit's fiat plan using `NVM_SUBSCRIBER_API_KEY`
- Card: visa *4242 (Stripe test card, enrolled via portal)
- `resolve_scheme()` → `nvm:card-delegation`
- `list_payment_methods()` → found 1 card
- Token obtained (1640 chars), call succeeded (200 OK)
