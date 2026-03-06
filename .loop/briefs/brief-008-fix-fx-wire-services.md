# Brief: Fix FX Handler + Wire Services

**Branch:** brief-008-fix-fx-wire-services
**Model:** sonnet

## Goal

Fix the Frankfurter FX rates handler (it's async but the gateway calls handlers synchronously) and verify all services work. This is a cleanup brief before wiring portfolio revenue tracking.

## Context

Read these before starting:
- `src/services.py` — all handlers live here. The `_frankfurter_fx_rates` function at the bottom is `async def` but the gateway calls `service.handler(**(params or {}))` without await. It needs to be sync.
- `src/gateway.py` line 102 — `result = service.handler(**(params or {}))` — this is a sync call.
- All other handlers in services.py are sync and return `str` (JSON-encoded). The FX handler returns `dict`. Both need fixing.

## Tasks

1. **CRITICAL: Create `src/telemetry.py` if it doesn't exist.** The gateway imports `from src.telemetry import telemetry, TelemetryEvent` but the file may be missing. Check if it exists. If not, create it as a thin wrapper around `src/txlog.py`:
   - `TelemetryEvent` — a dataclass or dict-like class that holds event data (type, service_id, params, result, success, credits_charged, latency_ms, timestamp, etc.)
   - `Telemetry` class with:
     - `emit(event: TelemetryEvent)` — logs to the txlog (maps to txlog.log())
     - `count_calls(service_id, window_minutes=15)` — delegates to txlog
     - `get_recent(n, event_type=None)` — returns recent events, optionally filtered by type
     - `get_stats()` — returns summary dict (total calls, revenue, success rate, per-service counts)
   - Module-level singleton: `telemetry = Telemetry()`
   Read `src/gateway.py` to see exactly how telemetry is used (emit, count_calls, get_stats, get_recent with event_type filter) and make sure the interface matches.

2. **Convert `_frankfurter_fx_rates` from async to sync.** Replace `async with httpx.AsyncClient()` with sync `httpx.Client()` or just `httpx.get()`. Change return type from `dict` to `str` (JSON-encoded, matching all other handlers). Remove `async` keyword. Keep the same params and behavior.

3. **Verify all services by reading through each handler.** Check that:
   - Every handler is a sync function (not async)
   - Every handler returns `str` (JSON-encoded)
   - Every handler has a matching `catalog.register()` call
   - No handler references removed env vars (e.g., `FAL_KEY` should now be `GOOGLE_API_KEY`)
   Count total services, confirm it matches catalog registrations.

3. **Quick smoke test.** Import the catalog and verify all services are registered:
   ```python
   python -c "from src.services import catalog; print(f'{len(catalog.services)} services'); [print(f'  {s.service_id}: handler={s.handler is not None}') for s in catalog.services]"
   ```
   Fix any import errors or registration issues.

## Completion Criteria

- [ ] `src/telemetry.py` exists and gateway can import it
- [ ] `_frankfurter_fx_rates` is sync, returns JSON string
- [ ] All handlers are sync, return JSON strings
- [ ] All handlers have matching catalog.register() calls
- [ ] `from src.services import catalog` works without errors
- [ ] Service count matches expected (12 services)

## Verification

- `python -c "from src.services import catalog; assert len(catalog.services) >= 12, f'Only {len(catalog.services)} services'"` passes
- No `async def` in handler functions (catalog handlers only — other async code in the file is fine)
