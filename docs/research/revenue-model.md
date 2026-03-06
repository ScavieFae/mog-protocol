# Nevermined Revenue Model — What We Know

## The Transaction Lifecycle

```
1. REGISTER (seller)
   payments.agents.register_agent_and_plan(...)
   - Creates agent + plan on-chain
   - Sets price_config (free or token-priced)
   - Sets credits_config (how many credits granted, min/max per request)
   - No money moves here

2. SUBSCRIBE (buyer)
   payments.plans.order_plan(PLAN_ID)
   - Buyer subscribes to seller's plan
   - If get_free_price_config(): $0, buyer gets credits for free
   - If get_erc20_price_config(): buyer pays tokens (USDC etc), gets credits
   - This is the "Purchase" event on the Revenue page
   - Shows: plan name, consumer wallet, payment type, price, credits granted

3. GET TOKEN (buyer)
   payments.x402.get_x402_access_token(PLAN_ID)
   - Returns a signed Bearer token proving buyer has credits
   - No money moves here
   - Token is reusable across multiple calls

4. CALL (buyer → seller)
   POST /mcp with Bearer token
   - PaymentsMCP validates token
   - @mcp.tool(credits=N) declares cost
   - Credits are REDEEMED (burned) from buyer's balance
   - Handler executes, result returned
   - On-chain settlement on Base Sepolia
   - This is the "creditsRedeemed" in the _meta response

5. SETTLE (automatic)
   - Nevermined settles on-chain
   - tx hash appears in response _meta
   - But what actually settles? Credits? Tokens? Both?
```

## What We Configured

```python
# Our plan setup (setup_gateway.py)
price_config=get_free_price_config(),        # $0 to subscribe
credits_config=get_dynamic_credits_config(
    credits_granted=100,                      # buyer gets 100 credits
    min_credits_per_request=1,
    max_credits_per_request=10,
),
access_limit="credits",
```

- Subscription: FREE ($0.00)
- Credits granted: 100
- Credits burned per call: 1-10 depending on service
- Revenue received: $0.00

## What Shows on the Revenue Page

All 14 events show:
- Price: 0.00
- Credits: 100
- Type: Purchase (subscription events only)
- Currency: Native or USDC

We do NOT see individual credit burns (service calls) on the Revenue page.
Only subscription events appear.

## The Revenue Gap

Credits burn on every buy_and_call. We see tx hashes in responses:
```json
{
  "_meta": {
    "txHash": "0x5bd6639...",
    "creditsRedeemed": "1",
    "subscriberAddress": "0x863e...",
    "success": true
  }
}
```

But credits have no monetary value because our plan is free.
Credits are a metering mechanism, not a payment mechanism.
Nothing flows back to our wallet when credits burn.

## What Would Generate Actual Revenue

### Option 1: Token-priced subscription
```python
from payments_py.plans import get_erc20_price_config

price_config=get_erc20_price_config(
    token_address="0x...",  # USDC on Base Sepolia
    price=1_000_000,        # 1 USDC (6 decimals)
)
```
Buyer pays USDC to subscribe. We receive tokens.
Credits still meter usage, but the subscription itself costs money.

### Option 2: Per-credit token pricing
Unknown if this exists. The SDK has `get_dynamic_credits_config()`
but that only controls how many credits are granted and burned,
not what each credit is worth in tokens.

### Option 3: Stripe / card delegation
```
nvm:card-delegation scheme
```
Exists in the protocol but unclear sandbox support.
Requires buyer to pre-enroll a card. Shelved for hackathon.

## Open Questions (Ask Nevermined Staff)

1. **What counts as "revenue" on the leaderboard?**
   - Subscription payments only?
   - Credit burns?
   - On-chain token transfers?
   - Or is there no leaderboard and judges get data manually?

2. **Do credit burns have monetary value with free plans?**
   - If we use get_free_price_config(), do credit redemptions
     register as revenue anywhere?
   - Or is it purely metering with no settlement value?

3. **What token address for testnet USDC on Base Sepolia?**
   - If we switch to get_erc20_price_config(), what's the
     contract address for the accepted token in sandbox?
   - Do buyers need testnet USDC in their wallet, or does
     Nevermined handle this in sandbox?

4. **Can we re-register a plan with a new price_config?**
   - Or do we need a new plan ID?
   - If new plan ID, all existing subscribers would need to
     re-subscribe.

5. **How are judges tracking "economic behavior"?**
   - Transaction count?
   - Revenue?
   - Cross-wallet activity?
   - Diversity of buyers?
   - What's the actual scoring?

## What We Know For Sure

- 14 subscription events on-chain
- 4 external wallets subscribed (not ours)
- At least 1 external service purchase (hackathon_guide)
- Credit burns produce tx hashes on Base Sepolia
- Revenue page shows $0.00 because all plans are free
- Credits are minted on subscribe, destroyed on use, nothing returns to seller
- Changing to token-priced plans is a code change + re-registration
- Existing subscribers would need to re-subscribe to a new plan
