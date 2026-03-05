# Nevermined — x402 Facilitator Teardown

Nevermined positions itself as "AI billing and payments infrastructure" — the coordination layer between AI agents that need to pay each other. They're one of ~18 facilitators in the x402 ecosystem. The Ripple connection is unannounced — Mattie has intel that Nevermined has a relationship with Ripple to run an x402 facilitator for XRPL, but nothing public confirms this yet.

**Relevance to xrp402:** They'd be the incumbent if they ship XRPL support. Understanding what they actually have vs. what they market matters.

---

## What They Actually Have

### Facilitator (live)

Base URL: `https://facilitator.nevermined.app`

Endpoints:
- `POST /authorize` — create authorization tokens
- `GET /challenge` — construct x402 payment challenges
- `POST /verify` — verify payment proof
- `POST /meter` — submit usage signals (their extension to x402)
- `POST /settle` — execute on-chain settlement
- `GET /entitlements` — resolve credit/time-plan access

**Networks supported today:** Base mainnet, Base Sepolia. That's it. No XRPL, no Solana, no other EVM chains. They're a single-chain facilitator despite the multi-chain marketing.

### SDK

`@nevermined-io/payments` (TypeScript, v2.4.1) and `payments-py` (Python). The TS SDK handles agent registration, payment plans (credit-based and time-based subscriptions), and bearer token auth. Works with Next.js, Express, Fastify.

### Smart Contract Layer

This is where they go beyond vanilla x402:
- **AssetsRegistry** — registers agents/plans with pricing models
- **AgreementsStore** — tracks agreement states and conditions
- **PaymentsVault** — escrow and token balances
- **NFT1155Credits** — tokenized access rights (expirable, dynamic)

All EVM. Solidity contracts on Base. Their `nevermined-io/contracts` repo has the code.

### x402 Extensions

They've authored two spec extensions:
- **Smart Accounts Extension** — ERC-4337 account abstraction for programmable settlement (session keys, spending caps, batching)
- **Visa VIC Extension** — fiat payment integration (less substantiated than the smart accounts piece — may be more about Visa's broader VIC API ecosystem initiative than a Nevermined-specific extension)

**The Smart Accounts piece is their real differentiator.** Vanilla x402 uses EIP-3009 ("Transfer With Authorization") for settlement — literally just a token transfer. You can't express "pay, then execute business logic, then mint access, then split revenue" atomically. The extension replaces the settlement step with smart contract calls while keeping the x402 HTTP handshake unchanged.

What smart accounts actually solve for agents:
- **The autonomous spending problem** — An EOA (normal wallet) gives an agent either unlimited spending authority (agent has private key) or blocks on human approval (human has key). Neither works at scale. Smart accounts put rules *in the wallet*: session keys (24hr expiry), spending caps ($50/day), whitelists (only these contracts), batching (approve once, execute many). The agent gets scoped authority without a human in the loop.
- **Atomic pay-and-execute** — payment + fulfillment in one tx, no race condition
- **Escrow with conditions** — lock funds, release on milestone/SLA/dispute window
- **Revenue splits** — multi-party payouts, atomic

**Backward compatibility caveat:** The x402 flow is backward compatible, but settlement is not. Any facilitator can settle a vanilla EIP-3009 transfer. But settling "call Nevermined's contracts, deduct credits, mint access NFT, split revenue" requires a facilitator that understands Nevermined's contract layer. Resource servers advertising this extension effectively require Nevermined's facilitator. Classic embrace-and-extend — protocol stays open, valuable features route through their infrastructure. They've also filed [issue #639](https://github.com/coinbase/x402/issues/639) on Coinbase's x402 repo pushing for ERC-4337 in the core spec, which would dissolve this moat if adopted.

[source: https://nevermined.ai/blog/making-x402-programmable]

---

## What They Market vs. What Exists

| Claim | Reality |
|-------|---------|
| "Fiat & crypto settlement" | Base + USDC. Stripe integration mentioned but unclear how deep |
| "Cards, wallets, stablecoins, and credits" | Credits system is real. Card/wallet = Stripe passthrough? |
| "Sub-cent transaction tracking" | Metering endpoint exists. Unclear if sub-cent actually works on-chain |
| "<50ms p99 response time" | Plausible for verify — it's just signature checking |
| "SOC-2 Type II, ISO 27001, PCI SAQ-A, GDPR" | Enterprise compliance certs. Real if true — moat for institutional deals |
| "1-2% transaction fee" | Business model is take rate. No minimums, no lock-in |
| Multi-chain | **Base only.** The ecosystem page confirms it |

---

## Facilitator Endpoint Comparison (vs. xrp402)

| | **xrp402** | **Nevermined** |
|---|---|---|
| Health / metadata | `GET /` | — |
| What do you support? | `GET /supported` | — |
| Verify payment | `POST /verify` | `POST /verify` |
| Settle payment | `POST /settle` | `POST /settle` |
| Create auth tokens | — | `POST /authorize` |
| Construct payment challenge | — | `GET /challenge` |
| Usage metering | — | `POST /meter` |
| Credit/subscription lookup | — | `GET /entitlements` |

The shared core is verify and settle — that's the x402 spec. Nevermined's four extra endpoints reflect their more complex billing model: `/authorize` creates session tokens (ERC-4337 delegation), `/challenge` centralizes payment condition construction in the facilitator (xrp402 leaves this to the resource server), `/meter` tracks usage for billing, `/entitlements` checks existing access so clients can skip payment.

xrp402's facilitator is a **pure payment verifier and submitter** — stateless, never touches funds. Nevermined's is a **payment orchestrator** — manages authorization state, constructs challenges, tracks metering, resolves entitlements, AND does verify/settle. More like a billing system that speaks x402.

---

## Payment Pattern Comparison (vs. XRPL Native)

| Payment Pattern | Nevermined (EVM) | XRPL Native |
|---|---|---|
| **One-shot payment** | EIP-3009 signed transfer | Direct Payment — what xrp402 does today |
| **Escrow / held funds** | PaymentsVault smart contract | **Native Escrow** — protocol-level, time-based (FinishAfter/CancelAfter) and crypto-condition based |
| **Credits / prepaid balance** | NFT1155Credits + AssetsRegistry | **Payment Channels** — fund once on-chain, exchange signed claims off-chain (instant, free), settle when done |
| **Metered usage billing** | `/meter` endpoint + contract state | **Payment Channels** — each usage increment is a new off-chain claim for a higher amount, settle the final total |
| **Time-based subscription** | Smart contract with time bounds | **Escrow with FinishAfter/CancelAfter** — native time-locked funds |
| **Revenue splits** | Smart contract distributes to multiple parties | **Weakest spot.** No single native primitive. Multiple Payment objects, or wait for XLS-101d. |
| **Session delegation** | ERC-4337 smart accounts, session keys, spending caps | **Regular Keys** — secondary key pair authorized to sign. Simpler (no spending caps or time bounds), but core concept is native. |

Payment Channels are the XRPL feature that maps to most of what Nevermined built contracts for — credits, metering, micropayments. But XRPL's native primitives are powerful and closed: each does what it does with protocol-level guarantees, but you can't extend, compose, or build unexpected things on top of them. Nevermined's smart contract approach trades those guarantees for arbitrary composability — contracts calling contracts, new billing patterns nobody anticipated. Though in practice, that composability is internal to their stack: developers use Nevermined's SDK to interact with Nevermined's contracts, not remix them.

The gap narrows with XLS-101d WASM contracts, which would let XRPL have composability *with* native primitives. But that's AlphaNet, not mainnet.

---

## Architecture vs. xrp402

Their flow is the same three-party model but with extra steps:

```
Client → Server: GET resource
Server → Client: 402 + payment conditions
Client → Smart Account: create delegation with session key
Client → Server: GET resource + PAYMENT-SIGNATURE header
Server → Facilitator: POST /verify (check on-chain validity)
Server: fulfill request
Server → Facilitator: POST /settle (execute contracts, deduct credits, split revenue)
Client ← Server: 200 + result + proof
```

**Key difference from our flow:** They insert a smart contract layer between verify and settle. Verify checks the delegation is valid. Settle executes business logic (credit deduction, revenue splits, escrow release). This is more complex than our "verify the signed tx, submit it to the ledger" approach, but it enables things we can't do yet — subscriptions, metered billing, atomic pay-execute.

**Their bet:** x402 needs to be programmable to matter. One-shot payments per request are a demo, not a product.

**Our counter:** On XRPL, settlement IS the product. The whole point of x402 on XRPL is that payments settle on a purpose-built payment ledger with protocol-level guarantees. You don't need ERC-4337 and escrow contracts when the ledger has native escrow, payment channels, and 3-second finality.

<!-- riff id="nevermined-pattern" status="developing" could_become="interview_answer, blog" -->

**The Nevermined pattern worth noting:** Their core insight is that vanilla x402 (one payment per request) isn't enough for real agent commerce. Their answer is a smart contract layer *on top of* x402 that enables subscriptions, credits, metering, revenue splits — the full billing surface area. On EVM, that requires Solidity contracts. The question for XRPL: how much of that billing surface area is already covered by native primitives (payment channels, escrow, checks) without needing a contract layer at all?

<!-- /riff -->

---

## Agent Registration & Identity

Nevermined's "agent registration" is platform onboarding, not ERC-8004. You register your agent with Nevermined's system, attach a pricing plan (credits or time-based), and get a DID plus wallet. You can't register an agent without first configuring a pricing plan — it's a billing system with discovery bolted on.

**DID format:** `did:nv:<64-hex-chars>` (e.g., `did:nv:bcf381cd7af79667f09883247af0dc999b08b5cd8a870e903ccb4eff408e41bc`). W3C DID spec compliant, `nv` is their own method. DID stored on-chain (Base), DDO (metadata) stored off-chain. Registered via their DIDFactory smart contract.

**What's "decentralized" about it:** The identifier is on a public chain, so verification is permissionless — anyone can confirm a `did:nv:` exists without asking Nevermined. But creation, resolution, and usefulness all flow through their infrastructure. It's more quasi-permissionless than decentralized. The blockchain buys tamper-evidence (proves agent X was registered at time Y with checksum Z), not portability or platform independence.

**Compare to:** Privado ID (formerly Polygon ID) where credentials live in the user's wallet with ZK proofs, chain-agnostic and reusable. Or ERC-8004 where identity is an NFT on Ethereum any platform can read. Or `did:ethr:` where the identifier *is* your Ethereum address and resolution is just reading a public contract. Nevermined's `did:nv:` is tightly coupled to their billing contracts, which is why they rolled their own rather than using existing DID infrastructure — but the cost is lock-in.

Their SDK also publishes A2A agent cards (`.well-known/agent.json`), bridging Nevermined identity with Google's A2A discovery protocol.

---

## The XRPL Question

Nothing public connects Nevermined to XRPL. Their entire stack is EVM — Solidity contracts, ERC standards (4337, 3009, 712, 1155), Base deployment. Porting to XRPL would mean:

1. **No smart contracts** (yet) — their AssetsRegistry, AgreementsStore, PaymentsVault, NFT1155Credits contracts have no equivalent on XRPL mainnet. XLS-101d WASM contracts are on AlphaNet but not mainnet.
2. **Different signing** — XRPL uses secp256k1/ed25519, not EIP-712 typed data signing. Their entire auth flow would need rewriting.
3. **Different asset model** — XRPL has native XRP, trust lines for issued currencies (RLUSD), and MPTs. No ERC-20/ERC-1155 equivalents.
4. **XRPL EVM sidechain** — the path of least resistance. They could deploy their EVM contracts on the XRPL EVM sidechain (launched June 2025) and bridge to native XRPL for settlement. This is probably what the Ripple relationship enables.

**Most likely scenario:** Nevermined deploys on the XRPL EVM sidechain, not native XRPL. They keep their Solidity stack, get the "XRPL" branding for Ripple partnership announcements, and bridge to native RLUSD for settlement. This would be faster to ship but wouldn't be a native XRPL facilitator.

**What this means for xrp402:** We're building native. If Nevermined goes the EVM sidechain route, we're not really competing — we're the native XRPL facilitator, they're the EVM-compatible one. Different markets, different tradeoffs.

---

## x402 V2: The Ground Shifting Under Nevermined

x402 V2 launched with extensions as a first-class concept and new payment schemes beyond `exact`. This changes the competitive picture:

- **`upto` scheme** — pay up to an amount based on consumption. This is metered billing at the protocol level, which was a Nevermined differentiator.
- **`deferred`, `conditional`, `recurring`** — on the roadmap. Subscriptions and conditional payments built into the standard.
- **SIWx (Sign-In-With-X)** — wallet-based identity linking auth to previous payments. Pay once, prove identity later.
- **Bazaar (Discovery)** — facilitators index x402-enabled APIs. Open, self-organizing discovery.

x402 V2 is starting to absorb the simpler billing patterns that justified Nevermined's smart contract layer. Nevermined's remaining moat narrows to what the protocol *can't* do natively: atomic multi-step settlement, escrow with arbitrary conditions, revenue splits, programmable session-key delegation. The complex stuff stays differentiated; the simple stuff (metering, subscriptions) may get commoditized by the standard.

[source: https://www.x402.org/writing/x402-v2-launch]

---

## Strengths (Real)

- **Enterprise compliance certs** — SOC-2, ISO 27001, PCI. If real, this is a genuine moat. Getting these takes months and money.
- **Credit/subscription model** — solves x402's biggest UX problem (wallet popup per request). Buy credits once, use many times.
- **Metering** — the `/meter` endpoint is a real extension to x402. Usage-based billing needs something like this.
- **Head of growth** Mattie knows — relationship matters, especially if Ripple is making introductions.

## Weaknesses

- **Single-chain** — Base only, despite marketing otherwise. Shipping XRPL support means porting an entire EVM stack.
- **Complexity** — smart accounts, session keys, escrow contracts, NFT credits. Lots of moving parts. More surface area for bugs, more things to audit.
- **No public XRPL work** — no repos, no docs, no blog posts. Either very early or vaporware.
- **Closed facilitator** — their facilitator at `facilitator.nevermined.app` is hosted. No self-hosted option visible. Centralization risk for a "decentralized" protocol.

---

<!-- riff id="cross-chain-authority" status="developing" could_become="interview_answer, blog" -->

**The cross-chain authority problem:** Smart account constraints (spending caps, session keys, whitelists) live in a smart contract on a specific chain. If an agent needs to pay on a different chain, those constraints don't travel. The Base smart account says "max $5/day" — but the agent's XRPL wallet has no idea that rule exists.

This is why cross-chain *orchestration* is a harder problem than cross-chain *bridging*. Bridging moves tokens. Orchestration moves *authority* — "this agent is allowed to do X" needs to be legible and enforceable across chains with completely different execution models. An ERC-4337 session key means nothing on XRPL. An XRPL regular key means nothing on Ethereum.

Three options, none great:
1. Duplicate constraints on every chain — but XRPL doesn't have smart contracts (mainnet), and syncing parallel deployments across EVM chains is its own problem
2. Cross-chain orchestration layer that enforces constraints above individual chains — the agent asks before spending, orchestrator checks global budget. This is probably where the market goes.
3. Keep all spending on one chain — the simplest answer, and probably why Nevermined is Base-only

This also explains why the "just use the EVM sidechain" path is tempting but insufficient: smart account constraints stay on the sidechain, but bridging to native XRPL for settlement drops back to an unconstrained key.

XRPL's gap here: Regular Keys give you key delegation but with no spending caps or time bounds. An XRPL agent with a regular key has the same unlimited authority problem as an EOA. Payment channels help (the channel funding *is* the spending cap), but that's not the same as per-transaction programmable authorization. This is a real limitation for autonomous agent payments on XRPL today.

<!-- /riff -->

---

## Practical Builder Guide: What You Need to Build With Nevermined Tomorrow

### The Mental Model

Nevermined is **Stripe for AI agents**. You register a service, attach a pricing plan, and Nevermined handles access control, credit metering, and settlement. The x402 protocol is the transport — HTTP 402 responses tell clients how to pay, `payment-signature` headers carry proof-of-payment. But Nevermined wraps this in a managed billing layer so you never touch wallets, smart contracts, or token transfers directly.

Three entities matter:
1. **Agent** (your service) — has endpoints, metadata, a DID
2. **Plan** (your pricing) — credits-based, time-based, or pay-as-you-go
3. **Subscriber** (your customer) — buys a plan, gets an access token, sends it in headers

### Step 0: Get Credentials

```bash
# Get API key from https://app.nevermined.app
export NVM_API_KEY="sandbox:your-api-key"
export BUILDER_ADDRESS="0xYourWalletAddress"
```

Two environments: `sandbox` (Base Sepolia testnet) and `live` (Base mainnet). Sandbox uses test USDC.

### Step 1: Install SDK

```bash
npm install @nevermined-io/payments   # TypeScript
pip install payments-py                # Python
```

### Step 2: Register Agent + Plan (One Call)

The SDK lets you register an agent and its pricing plan atomically:

```typescript
import { Payments } from '@nevermined-io/payments'

const payments = Payments.getInstance({
  nvmApiKey: process.env.NVM_API_KEY,
  environment: 'sandbox',
})

// USDC on Base Sepolia
const USDC = '0x036CbD53842c5426634e7929541eC2318f3dCF7e'

const { agentId, planId } = await payments.agents.registerAgentAndPlan(
  // Agent metadata
  { name: 'My Weather Agent', tags: ['weather', 'api'] },
  // Endpoints to monetize
  { endpoints: [{ 'POST': 'https://my-agent.example.com/api/weather' }] },
  // Plan metadata
  { name: 'Standard Plan', description: '100 weather lookups' },
  // Price: 10 USDC (6 decimals)
  payments.plans.getERC20PriceConfig(10_000_000n, USDC, process.env.BUILDER_ADDRESS),
  // Credits: 100 total, 1 per request
  payments.plans.getFixedCreditsConfig(100n, 1n),
)
```

### Plan Types Available

| Type | Method | What it does |
|------|--------|-------------|
| Fixed credits | `registerCreditsPlan()` + `getFixedCreditsConfig(total, perRequest)` | Buy N credits, each request burns some |
| Dynamic credits | `getDynamicCreditsConfig(total, min, max)` | Credits per request vary (e.g., by complexity) |
| Time-based | `registerTimePlan()` + `getExpirableDurationConfig(seconds)` | Unlimited use for a duration |
| Pay-as-you-go | `getPayAsYouGoPriceConfig()` + `getPayAsYouGoCreditsConfig()` | Settle per-request in USDC |
| Free trial | `registerCreditsTrialPlan()` / `registerTimeTrialPlan()` | Limited free access |

Price configs: `getERC20PriceConfig()` (USDC), `getFiatPriceConfig()` (Stripe), `getFreePriceConfig()`, `getNativeTokenPriceConfig()`.

### Step 3: Protect Your Endpoints

**Option A: Express middleware (easiest)**

```typescript
import express from 'express'
import { paymentMiddleware } from '@nevermined-io/payments/express'

const app = express()

// One line — all payment logic handled
app.use(paymentMiddleware(payments, {
  'POST /api/weather': { planId: PLAN_ID, credits: 1 },
  'POST /api/forecast': { planId: PLAN_ID, credits: 5 },
}))

// Your route handlers stay clean — no payment code
app.post('/api/weather', (req, res) => {
  res.json({ temp: 72, conditions: 'sunny' })
})
```

The middleware:
1. Checks for `payment-signature` header
2. Returns `402 Payment Required` with base64-encoded payment requirements if missing
3. Calls `facilitator.verifyPermissions()` — checks subscriber has credits
4. Runs your handler
5. Calls `facilitator.settlePermissions()` — burns credits, returns receipt in `payment-response` header

**Option B: Manual verify/settle (any framework)**

```typescript
import { buildPaymentRequired } from '@nevermined-io/payments'

// In your request handler:
const token = req.headers['payment-signature']
if (!token) {
  const paymentRequired = buildPaymentRequired(PLAN_ID, {
    endpoint: '/api/weather',
    agentId: AGENT_ID,
    httpVerb: 'POST',
  })
  // Return 402 with base64-encoded payment requirements
  const encoded = Buffer.from(JSON.stringify(paymentRequired)).toString('base64')
  return res.status(402).setHeader('payment-required', encoded).json({ error: 'Payment Required' })
}

// Verify (non-destructive — checks balance without burning)
const verification = await payments.facilitator.verifyPermissions({
  paymentRequired,
  x402AccessToken: token,
  maxAmount: 1n,
})

if (!verification.isValid) {
  return res.status(402).json({ error: verification.invalidReason })
}

// ... do your work ...

// Settle (destructive — burns credits)
const settlement = await payments.facilitator.settlePermissions({
  paymentRequired,
  x402AccessToken: token,
  maxAmount: 1n,
  agentRequestId: verification.agentRequestId, // for observability tracking
})
// settlement.creditsRedeemed, settlement.remainingBalance
```

### Step 4: Client Side — Buying and Using

```typescript
// Subscriber buys the plan (triggers on-chain USDC transfer)
await payments.plans.orderPlan(PLAN_ID)

// Check balance
const balance = await payments.plans.getPlanBalance(PLAN_ID)
// balance.credits, balance.isValid

// Generate x402 access token (creates session key delegation)
const { accessToken } = await payments.x402.getX402AccessToken(
  PLAN_ID,
  AGENT_ID,
  100,           // redemptionLimit — max 100 uses
  '50000000',    // orderLimit — max 50 USDC in wei for auto top-up
  '2025-03-01T00:00:00Z', // expiration
)

// Use it
const response = await fetch('https://my-agent.example.com/api/weather', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'payment-signature': accessToken,  // x402 header
  },
  body: JSON.stringify({ city: 'Seattle' }),
})
```

The access token is a base64-encoded blob containing:
- The subscriber's wallet address
- Session keys with scoped permissions (burn credits, order more)
- Plan ID and agent ID
- Expiration and limits

**Key insight: the token is generated once and reused.** Each request doesn't require a new wallet signature. The session key delegation means the subscriber approves once, and the token works for N requests until credits run out or it expires. This is what makes their UX viable — no wallet popup per API call.

### MCP Integration

For MCP (Model Context Protocol) tools, Nevermined wraps the payment layer around MCP's tool interface:

```typescript
// Register an MCP tool with payment
payments.mcp.registerTool(
  'weather.today',
  {
    title: "Today's Weather",
    description: 'Get weather for a city',
    inputSchema: { type: 'object', properties: { city: { type: 'string' } } },
  },
  async (args) => ({
    content: [{ type: 'text', text: `Weather in ${args.city}: Sunny, 25C` }],
  }),
  { credits: 1n },  // Cost per invocation
)
```

### A2A (Agent-to-Agent) Integration

For Google's A2A protocol, Nevermined publishes agent cards with payment metadata at `/.well-known/agent.json`:

```json
{
  "capabilities": {
    "streaming": true,
    "extensions": [{
      "uri": "urn:nevermined:payment",
      "params": {
        "paymentType": "dynamic",
        "credits": 1,
        "planId": "<planId>",
        "agentId": "<agentId>"
      }
    }]
  }
}
```

The SDK provides `payments.a2a.start()` to run an A2A server with payment enforcement, and `payments.a2a.getClient()` for consuming paid A2A agents.

### Dynamic Pricing (Variable Credits)

Credits per request don't have to be fixed. The Express middleware accepts a function:

```typescript
app.use(paymentMiddleware(payments, {
  'POST /api/generate': {
    planId: PLAN_ID,
    // Credits calculated based on request content
    credits: (req, res) => {
      const tokens = estimateTokens(req.body.prompt)
      return Math.ceil(tokens / 100)  // 1 credit per 100 tokens
    },
  },
}))
```

For settle, you can also use `marginPercent` (0-10) to add a margin on top of actual cost, or `batch: true` for multi-step workflows where you settle once at the end.

### Protocol API (REST, No SDK)

Everything the SDK does maps to REST endpoints. The full protocol API:

**Agent Management:**
- `POST /agents` — register agent
- `GET /agents` — list agents
- `PUT /agents/:id` — update agent
- `POST /agents/:id/activate` / `deactivate` — toggle availability

**Plan Management:**
- `POST /plans` — create plan
- `GET /plans` — list plans
- `PUT /plans/:id` — update plan
- `POST /plans/:id/toggle` — enable/disable
- `POST /agents/:id/plans` — associate plan with agent

**Access & Payment:**
- `POST /plans/:id/order` — purchase a plan (triggers on-chain payment)
- `GET /plans/:id/balance` — check credit balance
- `POST /plans/:id/redeem` — burn credits manually
- `POST /plans/:id/mint` — mint credits (builder only)

**x402 Facilitator:**
- `POST /permissions` — create permission (generate access token)
- `GET /permissions/:id` — get permission details
- `GET /permissions` — list permissions (paginated)
- `DELETE /permissions/:id` — revoke permission
- `POST /verify` — verify access token (non-destructive)
- `POST /settle` — settle/burn credits (destructive)

**Requests/Observability:**
- `POST /requests/init` — initialize request tracking
- Track subtasks, costs, margins

### x402 Scheme: `nvm:erc4337`

Nevermined's custom x402 scheme identifier is `nvm:erc4337`. The 402 response looks like:

```json
{
  "x402Version": 2,
  "resource": { "url": "/api/weather", "mimeType": "application/json" },
  "accepts": [{
    "scheme": "nvm:erc4337",
    "network": "eip155:84532",
    "planId": "123456789",
    "extra": { "agentId": "987654321", "httpVerb": "POST" }
  }],
  "extensions": {}
}
```

They also support `nvm:card-delegation` for fiat (Stripe) payments — same x402 flow but settlement goes through credit card processing instead of on-chain.

### What's Actually Happening On-Chain

When you `orderPlan()`: USDC transfers from subscriber wallet to Nevermined's PaymentsVault contract on Base. NFT1155Credits are minted to the subscriber — these represent their prepaid access rights.

When you `settlePermissions()`: The facilitator burns credits from the subscriber's NFT1155 balance. No USDC moves per-request — money moved at purchase time, credits are the accounting layer.

For pay-as-you-go: USDC settles per request through the smart account's session key delegation. The access token contains session keys that can execute the transfer without the subscriber's direct approval.

### CLI Alternative

Nevermined also has a CLI for managing agents and plans without code:

```bash
# Install
npm install -g @nevermined-io/cli

# Configure
nvm config set apiKey $NVM_API_KEY

# Register and manage
nvm agent register --name "My Agent" --endpoint https://...
nvm plan create --name "Standard" --credits 100 --price 10
nvm plan order <planId>
nvm plan balance <planId>
nvm agent query <agentId> --token <accessToken>
```

---

## Open Questions

- What's the actual structure of the Ripple relationship? Grant? Partnership? Just "we'll support your chain"?
- Are they targeting native XRPL or the EVM sidechain?
- Timeline? If they're months away, we have runway.
- Would they be interested in integrating xrp402 rather than building their own native XRPL facilitator? (Mattie's relationship with their head of growth could open this door.)

---

## Sources

- https://nevermined.ai/facilitator
- https://nevermined.ai/docs/solutions/agent-to-agent-monetization
- https://nevermined.ai/blog/making-x402-programmable
- https://nevermined.ai/product
- https://www.x402.org/ecosystem
- https://github.com/nevermined-io/payments
- https://github.com/nevermined-io/contracts
- https://docs.nevermined.app/ — main documentation hub
- https://docs.nevermined.app/llms.txt — full documentation index
- https://docs.nevermined.app/docs/integrate/quickstart/5-minute-setup — quickstart guide
- https://docs.nevermined.app/docs/getting-started/core-concepts — core concepts
- Source code: `nevermined-io/payments` repo — `src/x402/facilitator-api.ts`, `src/x402/token.ts`, `src/x402/express/middleware.ts`
- https://github.com/nevermined-io/hackathons — hackathon starter kit with buyer/seller/MCP/Strands agents

---

## Hackathon Starter Kit — Technical Breakdown

Source: https://github.com/nevermined-io/hackathons

This repo is Nevermined's developer onboarding surface — working examples that show how to build agents that pay each other. Four example agents, all Python, all using the same core patterns.

### Technical Stack

**Python 3.10+** with Poetry for dependency management. No TypeScript agents in the repo (though TS SDKs exist separately). Core dependencies:

| Dependency | Version | Role |
|---|---|---|
| `strands-agents` | >=1.0.0 | AWS's agent framework (tool orchestration, system prompts, model abstraction) |
| `payments-py` | >=1.3.3 | Nevermined's Python SDK — x402 tokens, A2A payment handling, `@requires_payment` decorator |
| `fastapi` | ^0.120.0 | HTTP server for x402 mode |
| `uvicorn` | >=0.34.2 | ASGI server |
| `httpx` | ^0.28.0 | HTTP client |
| `openai` | ^1.40.0 | LLM provider (default: gpt-4o-mini) |
| `langchain-openai` + `langgraph` | >=0.3.0 | Alternative agent framework (LangGraph mode) |
| `sse-starlette` | >=2.0 | Server-sent events for streaming |
| `boto3` | >=1.35.0 | AWS SDK (for AgentCore deployment) |

**Strands SDK** is the default agent framework — it's AWS's open-source agentic SDK (not LangChain). Tools are defined with `@tool` decorators and the agent does autonomous tool selection based on system prompts. The repo also includes LangGraph alternatives (`agent_langgraph.py`, `langgraph_agent.py`) showing framework interop.

**Three deployment targets:** local (FastAPI + OpenAI), AWS AgentCore (Bedrock LLM), and a React web frontend for the buyer.

### How the Seller Agent Works

The seller is the simpler side. It exposes three tools at different price points:

```python
@tool(context=True)
@requires_payment(payments=payments, plan_id=PLAN_ID, credits=1, agent_id=NVM_AGENT_ID)
def search_data(query: str, max_results: int = 5, tool_context=None) -> dict:
    """Search the web for data. Costs 1 credit per request."""
    return search_web(query, max_results)  # DuckDuckGo Instant Answer API

@tool(context=True)
@requires_payment(payments=payments, plan_id=PLAN_ID, credits=5, agent_id=NVM_AGENT_ID)
def summarize_data(content: str, focus: str = "key_findings", tool_context=None) -> dict:
    """Summarize content with LLM-powered analysis. Costs 5 credits."""
    return summarize_content_impl(content, focus)

@tool(context=True)
@requires_payment(payments=payments, plan_id=PLAN_ID, credits=10, agent_id=NVM_AGENT_ID)
def research_data(query: str, depth: str = "standard", tool_context=None) -> dict:
    """Full market research with citations. Costs 10 credits."""
    return research_market_impl(query, depth)
```

The `@requires_payment` decorator from `payments-py` is the key abstraction. It wraps each tool so that:
1. Before execution, it checks for a valid x402 access token in the invocation state
2. If no token: returns a `PaymentRequired` error that the FastAPI wrapper translates to HTTP 402
3. If valid token: executes the tool, then settles credits on Nevermined's backend

**Two server modes:**

1. **HTTP/x402 mode** (`agent.py`) — FastAPI server on port 3000. The `POST /data` endpoint reads `payment-signature` from headers, passes it as `invocation_state` to the Strands agent, and the `@requires_payment` decorator handles verification internally. Also exposes `GET /pricing` (free) and `GET /stats` (free).

2. **A2A mode** (`agent_a2a.py`) — Full A2A-compliant server on port 9000. Serves `/.well-known/agent.json` with a Nevermined payment extension (`urn:nevermined:payment`). Uses `PaymentsRequestHandler` from `payments-py` to validate payment at the A2A message level. Here, tools are **plain** (no `@requires_payment`) because payment handling moves up to the request handler layer. Credits are calculated post-execution by scanning which tools the agent called:

```python
def _calculate_credits(self, messages: list) -> int:
    """Scan agent messages for tool_use to determine total credits."""
    total = 0
    for msg in messages:
        for block in msg.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name", "")
                credits = self._credit_map.get(name, 1)
                total += credits
    return total or 1  # minimum 1 credit per request
```

**Self-registration:** In A2A mode, the seller can auto-register with a buyer using `--buyer-url`. It sends a JSON-RPC message to the buyer's registration server with its own URL. The buyer then fetches the seller's agent card and adds it to an in-memory registry.

### How the Buyer Agent Works

The buyer is the more complex side. It doesn't use `@requires_payment` — instead, it *generates* payment tokens and *sends* them.

**Core flow (x402 HTTP mode):**
1. `discover_pricing` — `GET /pricing` from the seller, returns tiers and costs
2. `check_balance` — queries Nevermined API for remaining credits on the subscribed plan, plus local budget tracking
3. `purchase_data` — the money move:
   - Resolves payment scheme (`resolve_scheme` determines if it's crypto or fiat/card-delegation)
   - Calls `payments.x402.get_x402_access_token(plan_id, agent_id, token_options)` to generate an access token
   - POSTs to `{seller_url}/data` with `payment-signature: {token}` header
   - Seller verifies, executes, settles, returns data

**Core flow (A2A mode):**
1. `list_sellers` — reads the in-memory `SellerRegistry` (populated by seller auto-registration)
2. `discover_agent` — fetches `/.well-known/agent.json`, parses the `urn:nevermined:payment` extension for plan ID, agent ID, pricing
3. `check_balance` — same as above
4. `purchase_a2a` — uses `PaymentsClient` from `payments-py` which wraps the A2A protocol with automatic x402 token injection. Sends a standard A2A `MessageSendParams`, streams back SSE events, extracts the final completed response and `creditsUsed` from metadata.

**Budget management:** Thread-safe `Budget` class tracks daily and per-request spending limits in-memory. Checked before every purchase. Resets daily. Not persisted — session-scoped only.

**Token generation — the interesting part:**

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

This is where fiat meets crypto. `nvm:card-delegation` is a payment scheme where the buyer delegates spending authority from an enrolled credit card. The token carries a spending limit and duration — this is the fiat equivalent of the smart account session key pattern.

### Nevermined Payment Integration — How It Actually Works

The payment flow has three layers, and the hackathon kit shows all of them:

**Layer 1: Payments SDK initialization** — both buyer and seller create a `Payments` instance with their API key and environment. This connects to Nevermined's backend (not directly to the blockchain).

```python
payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)
```

**Layer 2: Token lifecycle** — the buyer generates an access token scoped to a plan and agent. The token is a base64 blob containing session keys, spending limits, and plan metadata. It's generated once and reused across requests until credits run out or it expires.

**Layer 3: Verify and settle** — the seller's `@requires_payment` decorator (or the A2A `PaymentsRequestHandler`) calls Nevermined's facilitator to verify the token is valid and the subscriber has credits. After the tool executes, it settles (burns credits). No on-chain transaction per request — credits are the accounting layer, the on-chain USDC transfer happened at subscription time.

**The asymmetry matters:** Sellers use `@requires_payment` (or `PaymentsRequestHandler`). Buyers use `payments.x402.get_x402_access_token()`. The seller's API key is a *builder* key (created the plan). The buyer's API key is a *subscriber* key (purchased the plan). Different keys, different permissions, same SDK.

### What the Starter Kit Actually Provides

**For hackathon teams building on Nevermined, you get:**

1. **Two working agents** that transact with each other out of the box (seller + buyer)
2. **Three payment protocols** demonstrated: x402 (HTTP headers), A2A (JSON-RPC + agent cards), MCP (tool-level payment)
3. **The `@requires_payment` decorator** — the simplest way to monetize any function. One line of code turns a function into a paid service.
4. **Multi-agent marketplace demo** — start a buyer, spin up multiple sellers with different tools/pricing, watch them discover each other and transact
5. **React web frontend** — chat UI with seller sidebar and activity log, SSE streaming
6. **AWS AgentCore deployment path** — Dockerfiles, AgentCore config, SigV4 signing for production deployment
7. **LangGraph alternative** — same patterns work with LangChain/LangGraph instead of Strands

**What you'd swap out for a real product:**
- The DuckDuckGo search (replace with Exa, Tavily, your own API)
- The in-memory budget/registry (replace with a database)
- The OpenAI model (gpt-4o-mini is the default, but it's model-agnostic via Strands)
- The pricing tiers (currently hardcoded, could be dynamic)

### Protocol Comparison (from the repo)

| | x402 (HTTP) | A2A (Agent-to-Agent) | MCP |
|---|---|---|---|
| Discovery | Custom `GET /pricing` | Standard `/.well-known/agent.json` | Tool registration |
| Communication | REST endpoints | JSON-RPC messages | Tool invocation |
| Payment transport | `payment-signature` header | `payment-signature` header | Per-tool `@requires_payment` |
| Interop | Custom protocol | Any A2A agent | Any MCP client |
| Payment handling | `@requires_payment` per tool | `PaymentsRequestHandler` per request | `@requires_payment` per tool |

<!-- riff id="nevermined-dx" status="draft" could_become="interview_answer" -->

**The developer experience insight:** Nevermined's real product isn't the facilitator or the smart contracts — it's the `@requires_payment` decorator. One line of code, any Python function becomes a paid service. The entire hackathon kit exists to show that off. Compare that to building x402 payment handling from scratch: you need to construct payment challenges, verify signatures, submit settlements, handle edge cases. Nevermined collapses all of that into a decorator. That's the SDK moat — not the protocol, not the contracts, but the developer experience of going from "I have a function" to "I have a paid API" in one line.

The question for xrp402: can we make the XRPL developer experience that frictionless? If monetizing a function on XRPL requires understanding payment channels, escrow conditions, and ledger submission... we lose to `@requires_payment`.

<!-- /riff -->
