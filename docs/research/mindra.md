# Mindra

**Website:** [mindra.co](https://mindra.co)
**Console:** [console.mindra.co](https://console.mindra.co) (currently in beta)
**Docs:** [docs.mindra.co](https://docs.mindra.co/docs)
**Stage:** Pre-seed
**Funding:** $1.2M from TQ Ventures (announced Nov 2025)
**In:** NVIDIA Inception Program
**HQ:** San Francisco (with R&D remaining in Turkey)

---

## What Mindra Is

Mindra is an **agentic orchestrator**—a platform that sits above your AI agents and coordinates them. Their framing: the "higher observer" that understands each agent's properties and routes tasks between them. You bring your own agents; Mindra handles the coordination, monitoring, and financial flow between them.

The bet they're making: as AI systems become multi-agent by default, you need infrastructure that handles not just *routing* but *payment*—agents buying and selling services from each other autonomously. That's the "Agentic Economy" thesis.

**Current product positioning shifts:** Their homepage calls them an "agentic orchestrator for adaptive workflows." Their docs landing page and `about` slug both call them "AI Agent Payment Infrastructure." These are different emphases. The payment angle seems to be where they're actually differentiating.

---

## Core Product

### console.mindra.co

The web console (currently beta) is where you:
- Define and configure workflows
- Register agents
- Monitor executions with metrics
- Manage wallets (FIAT + crypto)

Workflows can run in **parallel, sequential, or DAG mode**. Agents can be written in any language (Python, Go, TypeScript, Rust) and use any model (Claude, GPT, Llama, custom ML).

### API

Base endpoint: `https://api.mindra.co`

Three primary operations documented:
1. **Run Workflow** — trigger a workflow via REST
2. **Stream Events** — real-time execution updates via Server-Sent Events (SSE)
3. **Approvals** — human-in-the-loop for high-risk tool executions

Authentication appears to be API key based (standard for this category).

### Notable Platform Features

- **Anomaly detection + self-healing:** catches failures and hallucinations mid-execution, attempts recovery without manual intervention
- **Human-in-the-loop approvals:** built-in mechanism to pause and require human sign-off on high-risk actions
- **No-code workflow definition:** target audience is not just engineers—anyone should be able to compose workflows in the console
- **SOC 2 Type II compliant**, zero data retention policy

---

## The Payment/A2A Layer

This is the differentiating thesis. From what's surfaced across their site, docs landing, and the Turkish press coverage:

**Decentralized A2A payment protocol:** agents can transact with each other directly, with "near-zero fees." Built-in wallet system supports both FIAT and crypto.

The framing from their funding announcement:
> Mindra manages information flow, transaction security, and costs [between agents]. Agents can access external tools (maps, payment APIs) and make independent decisions.

The "Agentic Economy" pitch: autonomous agents aren't just pipelines—they're economic actors. An agent should be able to hire another agent, pay for a tool call, get reimbursed by an orchestrating system. Mindra wants to be the financial rails for that.

The documentation doesn't expose much detail about the payment protocol yet (it may be the differentiating feature they're being cagey about, or it's still early). The Crunchbase listing confirms this is a core part of the mission.

---

## Founders

### Zeynep Yorulmaz — CEO & Co-Founder

- Koç University (Istanbul) + TUM (Technical University of Munich)
- Previously: AI Engineer at Mercura (YC W25)
- Based San Francisco / Istanbul
- [LinkedIn](https://www.linkedin.com/in/zeynepyorulmaz/) | [GitHub: zeynepyorulmaz](https://github.com/zeynepyorulmaz)

On the funding announcement: "From here on out, I'm going all in on Mindra."

She came out of YC-adjacent ecosystem (Mercura was YC W25), has the technical background (AI engineering), and is building in SF while keeping Turkish roots. The Koç University connection is meaningful—it's Turkey's top technical university, comparable to a Bilkent or METU but with stronger startup culture.

### İlker Yörü — Co-Founder

Co-founder, also Koç University. Role beyond co-founder not surfaced.

### Deniz Soylular — Co-Founder

Co-founder, also Koç University. Role beyond co-founder not surfaced.

---

## How This Would Work at a Hackathon (Agents Buying/Selling Services)

The "Multi Agent Quest" at `ai-agent-bar-2026-prod.web.app` appears to be in this space—agents competing in an orchestration context. The setup for a hackathon where agents buy/sell services would look something like this on Mindra:

**Registration:** Each team registers their agent(s) in the Mindra console. The agent gets an identity and a wallet.

**Service exposure:** An agent that offers a service (say, a data retrieval agent) publishes itself to the orchestrator with a price. The A2A payment protocol handles the billing.

**Orchestration:** When an orchestrating agent needs to call a service, Mindra routes the request, deducts from the caller's wallet, credits the service provider.

**Monitoring:** All transactions and executions stream through the Mindra console in real-time via SSE.

**Settlement:** Could be FIAT or crypto depending on hackathon setup—the wallet supports both.

The practical challenge: Mindra is still in beta. The A2A payment docs aren't fully public-facing yet. A hackathon using this stack would likely be early-adopter territory—expect rough edges, close collaboration with the Mindra team, and potentially needing to coordinate directly with them for wallet setup.

<!-- ?depth -->
<!-- This is worth going deeper on once their A2A protocol docs are more fully published. The payment layer is where this gets interesting—it's basically account abstraction but for agent economics. -->

---

## Positioning in the Landscape

The workflow orchestration layer is crowded (LangGraph, CrewAI, AutoGen, Vertex AI Agent Builder, Microsoft Copilot Studio). Mindra is betting that **payment infrastructure** is the actual moat—that orchestrating agents is table stakes, but giving them wallets and letting them transact is the unlock.

This maps to the broader "agentic payments" wave: x402, Coinbase's USDC agent rails, Nevermined's NVM agent billing. Mindra's angle is more neutral (FIAT + crypto) and more orchestration-integrated than pure payment-layer plays.

Comparable positioning to Nevermined but with a stronger no-code workflow angle and enterprise security posture (SOC 2). Different from Nevermined's Web3-native, token-incentivized approach.

<!-- riff id="mindra-moat" status="draft" could_become="interview_answer" -->

The question I'd push on: is the orchestrator the right place to own the payment primitive? An orchestrator that also handles payments is powerful but creates lock-in risk—enterprises are cautious about putting financial rails inside a workflow tool they might swap out. The counter: if agents need real-time billing *during* execution, the orchestrator is actually the natural place for it. You can't do post-hoc settlement when an agent is buying 40 services in a single workflow run.

<!-- /riff -->

---

## Sources

- [mindra.co](https://mindra.co) — main site
- [docs.mindra.co](https://docs.mindra.co/docs) — documentation
- [Zeynep Yorulmaz — Crunchbase](https://www.crunchbase.com/person/zeynep-yorulmaz)
- [Mindra — Crunchbase](https://www.crunchbase.com/organization/mindra)
- [Koç University announcement (Turkish)](https://x.com/kocuniversity/status/1986689673868050644)
- [egirişim funding article (Turkish)](https://egirisim.com/2025/11/03/yerli-yapay-zeka-girisimi-mindra-tq-venturestan-1-2-milyon-dolar-yatirim-aldi/)
- [Zeynep Yorulmaz LinkedIn funding post](https://www.linkedin.com/posts/zeynepyorulmaz_im-excited-to-share-that-our-startup-mindra-activity-7391006242116345856-grRC)
- [Mindra enterprise blog post](https://mindra.co/blog/ai-agent-platform-comparison-the-complete-enterprise-evaluation-guide-for-2026)
