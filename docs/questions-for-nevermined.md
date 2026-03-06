# Questions for Nevermined Staff

Bring this to the venue. Check off answers as you get them.

---

## Plan & Agent Registration

- [ ] **Can one agent have multiple plans with different price configs?**
  We want one "Mog Markets" listing where the buyer picks free, card, or USDC at subscribe time. Right now `register_agent_and_plan()` always creates a new agent+plan pair. Is there an `add_plan()` or similar? Or do we need 3 separate agent listings?

- [ ] **Can we re-register a plan with a new price_config?**
  Or does changing from free to paid always require a new plan ID? If new plan ID, existing subscribers need to re-subscribe.

## Pricing & Payment

- [ ] **What's the correct USDC token address on Base Sepolia for `get_erc20_price_config()`?**
  We're using `0x036CbD53842c5426634e7929541eC2318f3dCF7e` (Circle USDC on Base Sepolia). Is that what the sandbox expects? Do buyers need testnet USDC in their wallet, or does Nevermined handle this?

- [ ] **`get_fiat_price_config()` fails in sandbox — "Unable to register agent and plan"**
  All 4 fiat/card plan registrations failed. USDC plans registered fine. Do we need to set up Stripe Connect on our account first? Or does fiat not work in sandbox?

- [ ] **For `get_fiat_price_config(amount)`, is `amount` in cents?**
  We're passing `100` for $1.00. Confirm units.

- [ ] **Do credit burns have monetary value with free plans?**
  With `get_free_price_config()`, credits are metering tokens. Does anything settle back to the seller wallet when credits burn? Or is revenue purely from the subscription payment?

## Leaderboard & Judging

- [ ] **What counts as "revenue" on the leaderboard?**
  Subscription payments only? Credit burns? On-chain token transfers? Or is there no automated leaderboard — do judges pull data manually?

- [ ] **How are judges tracking "economic behavior"?**
  Transaction count? Revenue amount? Cross-wallet activity? Diversity of buyers? What's the actual scoring rubric?

- [ ] **Can we see our own stats somewhere?**
  The Revenue page shows subscription events but not credit burns. Is there a dashboard for total credits redeemed, unique buyers, etc.?

## Technical

- [ ] **Can we use Anthropic instead of OpenAI for embeddings/LLM in PaymentsMCP?**
  Heard there might be a config option. We'd prefer to drop the OpenAI dependency.

- [ ] **Is there a way to query all subscribers to a plan programmatically?**
  We'd like to know how many unique buyers we have beyond what the Revenue page shows.

- [ ] **Card delegation — does it work in sandbox?**
  The `nvm:card-delegation` scheme exists in the protocol. Can we test it in sandbox or is it mainnet only?

---

*Last updated: March 5, 2026 ~17:00*
