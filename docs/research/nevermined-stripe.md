# Nevermined Stripe / Fiat Payment Integration — Research

**Date:** 2026-03-05
**Status:** Research only — based on local codebase analysis, existing research docs, and Nevermined starter kit code patterns. WebFetch, WebSearch, and Bash were unavailable during this session, so this draws entirely from what we've already documented plus SDK patterns visible in our research files.

---

## Summary

Nevermined supports fiat/Stripe payments alongside crypto through a payment scheme called `nvm:card-delegation`. This runs through the same x402 flow as crypto (`nvm:erc4337`) but routes settlement through Stripe-backed credit card processing instead of on-chain USDC transfers. The mechanism is real — it appears in the hackathon starter kit code and is listed as a Thursday demo topic ("Stripe/x402"). But the depth of integration, maturity, and documentation are unclear.

---

## How It Works

### Payment Schemes

Nevermined supports (at minimum) two x402 payment schemes:

| Scheme | Settlement | What It Does |
|--------|-----------|-------------|
| `nvm:erc4337` | On-chain (USDC on Base) | Smart account session keys, ERC-4337 account abstraction |
| `nvm:card-delegation` | Fiat (Stripe) | Credit card delegation, spending limits in USD cents |

The scheme is resolved per-plan. A plan is configured with either a crypto or fiat price config at registration time.

### Price Configuration (TypeScript SDK)

From our platform research, the TS SDK (`@nevermined-io/payments`) offers these price config methods:

```typescript
payments.plans.getERC20PriceConfig(amount, tokenAddress, builderAddress)  // USDC on-chain
payments.plans.getFiatPriceConfig(...)    // Stripe
payments.plans.getFreePriceConfig()       // Free plans
payments.plans.getNativeTokenPriceConfig(...)  // Native token (ETH)
```

`getFiatPriceConfig()` is the Stripe entry point for sellers. When a plan is registered with this config, buyers hitting that plan enter the `nvm:card-delegation` flow instead of the crypto flow.

### Buyer-Side Flow (from hackathon starter kit)

The starter kit's buyer agent includes this pattern for resolving payment schemes:

```python
def build_token_options(payments: Payments, plan_id: str) -> X402TokenOptions:
    scheme = resolve_scheme(payments, plan_id)  # crypto or fiat?
    if scheme != "nvm:card-delegation":
        return X402TokenOptions(scheme=scheme)
    # Fiat plan — fetch enrolled payment methods, build delegation config
    methods = payments.delegation.list_payment_methods()
    pm = methods[0]
    return X402TokenOptions(
        scheme=scheme,
        delegation_config=CardDelegationConfig(
            provider_payment_method_id=pm.id,
            spending_limit_cents=10_000,  # $100
            duration_secs=604_800,        # 7 days
            currency="usd",
        ),
    )
```

Key details from this code:

1. **`resolve_scheme(payments, plan_id)`** — queries Nevermined backend to determine if a plan uses crypto or fiat settlement. This is per-plan, not per-agent.
2. **`payments.delegation.list_payment_methods()`** — the buyer must have pre-enrolled a credit card (Stripe payment method). This returns their enrolled cards.
3. **`CardDelegationConfig`** — the fiat equivalent of smart account session keys:
   - `provider_payment_method_id` — Stripe payment method ID
   - `spending_limit_cents` — max spend (in USD cents, e.g., 10000 = $100)
   - `duration_secs` — how long the delegation is valid (e.g., 604800 = 7 days)
   - `currency` — USD
4. The resulting x402 access token carries this delegation config. The seller's `@requires_payment` decorator handles verification and settlement identically — it doesn't care whether the underlying scheme is crypto or fiat.

### The Card Delegation Model

This is not "pay $X per request via Stripe." It's a delegation model:

- The buyer enrolls a credit card with Nevermined (presumably through their web dashboard or API)
- When buying a fiat-priced plan, the buyer creates a delegation token: "I authorize up to $100 from this card over the next 7 days"
- The x402 access token carries this delegation
- Settlement happens through Nevermined's backend, which charges the Stripe payment method
- Credits are still the accounting layer — fiat just changes how credits are purchased, not how they're consumed

This mirrors the smart account pattern: session keys with spending caps on crypto, card delegation with spending limits on fiat. Same trust model, different rails.

---

## What We Know for Sure

1. **`getFiatPriceConfig()` exists** in the TypeScript SDK — sellers can register plans with Stripe-backed pricing
2. **`nvm:card-delegation` is a real payment scheme** — the hackathon starter kit buyer agent code handles it explicitly
3. **`payments.delegation.list_payment_methods()` exists** in the Python SDK — implies a `delegation` namespace on the `Payments` class
4. **`CardDelegationConfig` exists** in the Python SDK — structured config with spending limits and duration
5. **Nevermined is demoing "Stripe/x402" on Thursday** — it's listed in the hackathon agenda as a separate demo topic
6. **PCI SAQ-A compliance is claimed** — suggests Stripe integration is real (SAQ-A is the self-assessment for merchants who fully outsource cardholder data to a payment processor like Stripe)

---

## What We Don't Know

1. **How does card enrollment work?** The buyer needs `payments.delegation.list_payment_methods()` to return something — but how does a payment method get enrolled? Likely through the Nevermined web dashboard (`app.nevermined.app`), but we haven't confirmed this.

2. **Does `payments-py` have `getFiatPriceConfig()` equivalent?** The TS SDK clearly has it. The Python SDK's seller-side fiat plan registration is undocumented in our research. We only see the buyer-side code.

3. **Is `getFiatPriceConfig()` available in sandbox?** Sandbox uses Base Sepolia testnet for crypto. Unclear whether fiat/Stripe works in sandbox mode or only in `live` environment.

4. **What are the fees?** Nevermined claims "1-2% transaction fee" for their take rate. Stripe adds its own fees (typically 2.9% + $0.30 for US cards). Combined, a fiat transaction could cost 4-5% in fees.

5. **Can a single agent offer both schemes?** Can one plan accept either `nvm:erc4337` or `nvm:card-delegation`? Or does each plan have exactly one price config (and you'd need two plans for dual payment support)?

6. **Visa VIC Extension** — mentioned in Nevermined's marketing alongside fiat integration. Unclear if this is a separate thing from the Stripe integration or just Visa's broader VIC API ecosystem. "Less substantiated than the smart accounts piece."

7. **Settlement timing** — crypto settles at plan purchase time (USDC transfers, credits minted). Does fiat settle at purchase time too (Stripe charges the card upfront), or does it settle per-request?

---

## Can We Offer Both Blockchain and Stripe Payments?

**Probably, but with caveats.**

The architecture supports it conceptually — the payment scheme is per-plan, and an agent can have multiple plans. So you could register:

- Plan A: "Standard" — `getERC20PriceConfig()` — pay in USDC, 100 credits
- Plan B: "Standard (Fiat)" — `getFiatPriceConfig()` — pay via Stripe, 100 credits

Both plans point to the same agent endpoints. Buyers choose their plan based on their available payment method.

**The catch:** Our gateway (`find_service` + `buy_and_call`) currently passes a single `plan_id` per service. To support dual payment, we'd need to either:
- Register two plans per service and let buyers choose
- Modify `find_service` to return available payment options
- Or just pick one (crypto for hackathon, since everyone's on sandbox with free plans anyway)

**For the hackathon:** Everyone is on sandbox with free plans. The payment scheme doesn't matter operationally — `getFreePriceConfig()` bypasses both crypto and fiat settlement. The Stripe integration would only matter for the demo ("look, we support fiat too") or post-hackathon.

---

## Potential Potholes

1. **Card enrollment prerequisite** — Buyers need pre-enrolled Stripe payment methods. At a hackathon, nobody will have done this. This is a non-starter for day-of fiat payments between teams.

2. **Sandbox + Stripe unclear** — If fiat doesn't work in sandbox, it's irrelevant for hackathon transactions.

3. **Double fee stack** — Nevermined's 1-2% + Stripe's 2.9% + $0.30. For micro-transactions (the kind agent-to-agent commerce produces), the per-transaction fixed fee ($0.30) could eat the entire service value.

4. **Python SDK parity unknown** — The TS SDK clearly has `getFiatPriceConfig()`. The Python SDK (`payments-py`) shows buyer-side card delegation classes, but seller-side fiat plan registration might be TS-only or underdocumented. We're a Python shop.

5. **`payments.delegation` namespace** — appears in the buyer starter kit code but isn't documented in our research of the `payments-py` API surface. Could be newly added, or could be TS-only functionality that was shown as pseudocode in the Python examples.

6. **Settlement latency** — Stripe charges can take seconds to process. On-chain USDC transfers on Base are ~2s. But the credit model may abstract this away (charge card at plan purchase, not per-request).

---

## Relevance to Mog Protocol

**For the hackathon (today):** Low relevance. Everyone's on sandbox with free plans. The 8PM deadline is about having *any* paid transaction, not about payment method variety.

**For the demo (Friday):** Moderate relevance. Mentioning "we support both crypto and fiat rails" in a 3-minute demo could differentiate us, especially with Visa as a sponsor/speaker. But only if we can actually demonstrate it, which requires:
- Figuring out `getFiatPriceConfig()` in Python
- Having a test card enrolled
- Sandbox fiat support

**For post-hackathon:** High relevance. The whole thesis of "Stripe for AI agents" requires actually supporting Stripe. Dual-rail (crypto + fiat) is table stakes for any real marketplace.

**Recommendation:** Ask at the Nevermined Stripe/x402 demo today. Specific questions:
1. Does `getFiatPriceConfig()` work in sandbox?
2. How do buyers enroll a credit card? Is there a test mode?
3. Can one agent serve both fiat and crypto plans simultaneously?
4. Is the `delegation` namespace available in `payments-py` or only the TS SDK?

---

## Sources

All from local codebase:
- `docs/research/nevermined-platform.md` — primary source for payment scheme details, `getFiatPriceConfig()`, `nvm:card-delegation` flow, buyer starter kit code patterns
- `docs/research/nevermined-marketplace.md` — fiat payment scheme note, "Stripe without Shopify" framing
- `docs/research/hackathon-guide.md` — Thursday demo list includes "Stripe/x402"
- `docs/research/openapi-to-mcp-landscape.md` — XPack.ai and MCPize use Stripe (Web2) for comparison
- `docs/research/agent-orchestration-protocols.md` — "does agent commerce happen on-chain or through Stripe?" question
- `docs/research/felixcraft.md` — FelixCraft uses Stripe for product revenue ($16K+ lifetime), dual Stripe+USDC pricing
