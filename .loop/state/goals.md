# Goals

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon.

## Current Priority

**Full overnight build: portfolio, toolkit, surge pricing, website.** 8 briefs queued in order:

### Phase 1: Economic Core (007-010)
1. **brief-007-portfolio-core** — PortfolioManager class (budget, hypotheses, P&L). Must land first.
2. **brief-008-fix-fx-wire-services** — CRITICAL: create `src/telemetry.py` (missing!), fix async FX handler, verify all services.
3. **brief-009-gateway-revenue** — Wire portfolio into gateway (record_sale on buy_and_call, portfolio + traces in /health).
4. **brief-010-autonomous-investment** — Update conductor/worker prompts for portfolio-aware autonomous loop.

### Phase 2: Agent Toolkit (011-012)
5. **brief-011-toolkit-foundation** — Browse (Browserbase), email (AgentMail), credential vault, blockers, traces CLI.
6. **brief-012-research-and-services** — Exa social search, archive.ph, 5 new gateway services incl. circle_faucet.

### Phase 3: Polish + Growth (013-016)
7. **brief-013-surge-pricing-signals** — Multi-signal surge (demand pressure, velocity, cooldown). Expose in /health + website.
8. **brief-014-service-detail-page** — `/service/:id` page with stats, pricing, how-to-buy. Clickable flowers in garden.
9. **brief-015-buyer-onboarding** — Website `/connect` page + copy-to-clipboard code blocks. Two paths: CLI agent + human visitor.
10. **brief-016-ad-supported-free-tier** — Zeroclick (somi.ai) contextual ads in free-tier responses. `src/ads.py`, gateway injection, transparent labeling.

Execute in order. Each phase depends on the previous. The reviewer runs on every evaluation — do not skip it.

## Done Looks Like

- Portfolio tracks budget, hypotheses, P&L across the overnight run
- Telemetry exists and gateway starts without errors
- 17+ services in catalog, all sync, all tested
- Toolkit lets agents browse, email, store creds, report blockers
- Surge pricing reads demand + velocity + cooldown, not just raw count
- Website shows service detail pages with stats, pricing, uptime
- Website has `/connect` page with install instructions, copy-paste commands, GitHub link
- Free ad-supported tier works: contextual Zeroclick ads in free responses, paid plans ad-free
- Conductor uses reviewer checklist before every merge
- The loop ran overnight and made autonomous investment decisions

## Constraints

- Demo is Friday 5:30 PM. Everything must be stable by noon Friday.
- The human is asleep. The reviewer is your quality gate — no risky merges.
- Portfolio is JSON-on-disk (`data/portfolio.json`), not a database.
- All services in `src/services.py`. Gateway picks them up automatically.
- Toolkit API keys (BROWSERBASE, AGENTMAIL) may not be set — graceful degradation required.

Read `docs/specs/09-autonomous-portfolio.md` and `docs/specs/10-agent-toolkit.md` for architecture.
