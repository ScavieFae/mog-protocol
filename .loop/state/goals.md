# Goals

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon.

## Current Priority

**Autonomous portfolio management.** The agent has a 50-credit budget.
Goal: maximize ROI by discovering, validating, and wrapping APIs that buyers want.

## Done Looks Like

- Portfolio has 3+ hypotheses (some validated, some earning)
- At least 1 new service wrapped autonomously based on demand signals
- Portfolio shows positive ROI (earned > spent)
- Underperforming services identified (zero revenue after 1hr)
- data/portfolio.json has real P&L entries

## Investment Loop

The autonomous loop runs on every conductor heartbeat:

1. **Read portfolio** — `python -c "from src.portfolio import PortfolioManager; import json; print(json.dumps(PortfolioManager().get_summary(), indent=2))"`
2. **Read demand signals** — `curl -s https://beneficial-essence-production-99c7.up.railway.app/health | python -m json.tool`
3. **Propose hypotheses** — if budget > 5cr and demand signal exists, propose a new service hypothesis
4. **Validate winners** — dispatch scout/wrap briefs for hypotheses where `should_invest()` returns True
5. **Kill underperformers** — if a wrapped service has zero actual_revenue after 1hr, dispatch a KILL brief
6. **Reinvest** — track spend/earn in data/portfolio.json via PortfolioManager

## Phases Still Queued

### Phase 2: Agent Toolkit (011-012)
- **brief-011-toolkit-foundation** — Browse (Browserbase), email (AgentMail), credential vault, blockers, traces CLI.
- **brief-012-research-and-services** — Exa social search, archive.ph, 5 new gateway services incl. circle_faucet.

### Phase 3: Polish + Growth (013-016)
- **brief-013-surge-pricing-signals** — Multi-signal surge (demand pressure, velocity, cooldown). Expose in /health + website.
- **brief-014-service-detail-page** — `/service/:id` page with stats, pricing, how-to-buy. Clickable flowers in garden.
- **brief-015-buyer-onboarding** — Website `/connect` page + copy-to-clipboard code blocks. Two paths: CLI agent + human visitor.
- **brief-016-ad-supported-free-tier** — Zeroclick (somi.ai) contextual ads in free-tier responses. `src/ads.py`, gateway injection, transparent labeling.

## Constraints

- Demo is Friday 5:30 PM. Everything must be stable by noon Friday.
- The human is asleep. The reviewer is your quality gate — no risky merges.
- Portfolio is JSON-on-disk (`data/portfolio.json`), not a database.
- All services in `src/services.py`. Gateway picks them up automatically.
- Toolkit API keys (BROWSERBASE, AGENTMAIL) may not be set — graceful degradation required.

Read `docs/specs/09-autonomous-portfolio.md` and `docs/specs/10-agent-toolkit.md` for architecture.
