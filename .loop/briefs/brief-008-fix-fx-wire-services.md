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

1. **Convert `_frankfurter_fx_rates` from async to sync.** Replace `async with httpx.AsyncClient()` with sync `httpx.Client()` or just `httpx.get()`. Change return type from `dict` to `str` (JSON-encoded, matching all other handlers). Remove `async` keyword. Keep the same params and behavior.

2. **Verify all services by reading through each handler.** Check that:
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

- [ ] `_frankfurter_fx_rates` is sync, returns JSON string
- [ ] All handlers are sync, return JSON strings
- [ ] All handlers have matching catalog.register() calls
- [ ] `from src.services import catalog` works without errors
- [ ] Service count matches expected (12 services)

## Verification

- `python -c "from src.services import catalog; assert len(catalog.services) >= 12, f'Only {len(catalog.services)} services'"` passes
- No `async def` in handler functions (catalog handlers only — other async code in the file is fine)
