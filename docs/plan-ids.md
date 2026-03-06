# Mog Protocol — Plan & Agent IDs

Reference for all Nevermined agent and plan registrations. Queried live from the protocol on 2026-03-06.

Wallet: `0xca676aFBa6c12fb49Fd68Af9a1B400A577A3D58a`
Environment: sandbox
Gateway URL: `https://beneficial-essence-production-99c7.up.railway.app/mcp`

## Active Plans

### Mog Markets (consolidated gateway)

Agent ID: `48240718023678475399341842835225621286665771301570840304774956518509943562731`

The primary marketplace gateway. One agent, four plans. Runs `src/gateway.py` on Railway.

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Free Trial | Free | 3 | `52344374255582061362376941484417434816120915438329652344828008233054799099083` |
| 1 USDC | 1,000,000 micro-USDC | 1 | `27532529988899010156793041100542920191141640561034683667962973311488756564499` |
| 5 USDC | 5,000,000 micro-USDC | 10 | `6476982684193144215967979389100088950230657664983966011439423784485034538208` |
| 10 USDC | 10,000,000 micro-USDC | 25 | `29001175520261924428527314088863841592234134735048963980654691130902766240562` |

Env var used by gateway: `NVM_GATEWAY_AGENT_ID`, `NVM_GATEWAY_PLAN_ID` (the plan ID in .env points to an older registration — the gateway validates against the agent, not a single plan)

### Direct Server (original Exa service)

Agent ID: `102119794264899988176204818767775411831182066603815097908030667112394345128990`

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Mog Exa Credits | Free | 100 | `56064655340635502751035227097531184395429221588387852227963461103927877061446` |

Env: `NVM_AGENT_ID`, `NVM_PLAN_ID`

### Buyer Agent

Agent ID: `93388637799858335552510037471374655492292585204141402156744389359782115188647`

| Plan | Price | Credits | Plan ID |
|------|-------|---------|---------|
| Mog Buyer Credits | Free | 100 | `2338110013623542573308456469972416924511128365783263876018997397938588449987` |

Env: `NVM_BUYER_AGENT_ID`, `NVM_BUYER_PLAN_ID`

## Deprecated Plans

These are still registered on Nevermined but are no longer in use. Do not subscribe buyers to these.

### Hackathon Guide (paid) — BROKEN PRICE

Agent ID: `114789570719487711932976830211176344340646597109595305939357567796708985139074`

| Plan | Price | Credits | Plan ID | Issue |
|------|-------|---------|---------|-------|
| Hackathon Guide Access | 500,000,000 USDC | 100 | `1902103836764352954979658000025533972157035218331569325700184000206048487000` | Price is 500M USDC (registration bug — amounts field set to raw wei-scale number) |

Env: `NVM_GUIDE_AGENT_ID`, `NVM_GUIDE_PLAN_ID`

### setup_paid_plans.py agents — ONE AGENT PER TIER (superseded)

Created by `src/setup_paid_plans.py` using `register_agent_and_plan()`, which creates a separate agent for each tier. Superseded by the consolidated gateway agent above.

| Label | Agent ID | Plan ID |
|-------|----------|---------|
| Mog Markets USDC 1 Credit | `5027789741551863416379982593600047020218661947094647094592443475456445558956` | `60859172884142288164507163059546691936422006932528002950292307302678850457887` |
| Mog Markets USDC 10 Credits | `85863460214902670283518149981718612013052468454435930825826777072877992004936` | `87533285832696660011690943385915459855771974607401696593091951593047968932457` |
| Mog Markets USDC 20 Credits | `26362256032719680862657608533856503228352336116352372689675428778853218417830` | `107388892078779776783316313571466544272023725956678321074411803867639782898854` |
| Hackathon Guide USDC 1 Credit | `70017738080613879717066126226930242682259074906188166961853946497052825410503` | `97008325797120983960610080256091504556118455322568723324233173955711405894085` |

### Original free plans (commented out in .env)

First registrations. Separate agents for gateway and guide. The gateway free plan ID is still hardcoded in `onboard.py` — should be updated to the consolidated Free Trial plan.

| Label | Agent ID | Plan ID |
|-------|----------|---------|
| Gateway (free) | `48640872261251869030033108052183526690631027622085978188430169084356856647939` | `9661082042009636068072391467054896427087238025772062250717418964278633341785` |
| Guide (free) | `82912941131551845997559074870195234642138086895845726794338119104469804827506` | `80210700025910908916740431903389992758624785780559991487167394553102643149649` |

## Notes

- `onboard.py` still hardcodes the deprecated free gateway plan (`966108...1785`). Should point to the consolidated Free Trial plan (`523443...9083`).
- The Hackathon Guide paid plan has a 500M USDC price from a registration bug. Not usable. Guide content is available through the gateway's `hackathon_guide` service instead.
- `setup_paid_plans.py` used `register_agent_and_plan()` which creates a new agent per call. The consolidated gateway was built using `register_plan()` + `add_plan_to_agent()` to attach multiple tiers to one agent.
- The `.env` file has env vars for all deprecated plans (for reference). Only `NVM_GATEWAY_AGENT_ID` and `NVM_GATEWAY_PLAN_ID` are used by the running gateway.
