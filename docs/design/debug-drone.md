# Debug Drone — Autonomous Error Response Agent

## Overview

The Debug Drone (`mog-debugger`) is a 4th colony agent that activates when
buy_and_call errors occur. It reads failure telemetry, diagnoses the root cause,
attempts automated fixes, and reports to the colony.

## Trigger

On each tick, the drone checks telemetry for recent failed `buy_and_call` events.
If it finds failures it hasn't already investigated, it activates.

When idle (no errors), it skips its tick entirely — zero cost.

## Tools

| Tool | Purpose |
|------|---------|
| `check_errors` | Read recent failed buy_and_call events from telemetry |
| `inspect_service` | Get full service config (handler, URL, price, stats) |
| `test_service` | Call handler directly with sample params |
| `send_message` | Report findings to worker/supervisor |
| `check_marketplace` | Read full marketplace state |
| `patch_service` | Re-register a service with corrected URL/params |
| `self_buy` | Test through real Nevermined payment flow |

## Diagnosis Flow

```
1. check_errors → list of recent failures
2. For each failing service_id:
   a. inspect_service → is it in catalog? what's the handler?
   b. test_service → does the handler work when called directly?
   c. If handler works: problem is in params/auth → report to buyer via supervisor
   d. If handler fails: diagnose error type:
      - Timeout → upstream API slow → report, maybe increase timeout
      - 404/DNS → upstream API gone → kill service, notify worker
      - Auth error → API key issue → report to worker
      - Bad params → handler bug → attempt patch_service with fix
3. Send report to supervisor + worker
```

## System Prompt (Trinity-style)

The drone follows the same Trinity dispatch protocol as other agents:
- Receives DEBUG DISPATCH from supervisor when errors are flagged
- Sends DEBUG REPORT back with findings and actions taken
- Can send WRAP FAILED to worker if a service needs to be rebuilt

## Integration Points

- **Telemetry**: reads from `txlog` for failed events (same as _check_marketplace)
- **Catalog**: reads service config, can re-register with `patch_service`
- **Bus**: sends messages to worker/supervisor
- **Colony loop**: added as 4th agent, ticks after supervisor
- **HivePanel**: shows up as a 4th agent pill with rose/red color

## Guardrails

- Max 3 services investigated per tick
- Cannot kill services (only supervisor can)
- patch_service only works for mog-agent services (not hand-coded ones)
- Cooldown: won't re-investigate same service_id within 5 ticks
- Reports all actions to supervisor — doesn't act in the dark

## Colony Tick Order

```
scout → worker → supervisor → debugger
```

The debugger runs last so it can see errors from the current tick's self_buy
calls and has the most recent marketplace state.
