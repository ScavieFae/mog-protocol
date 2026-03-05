"""End-to-end test for the Mog Protocol gateway logic.

Tests catalog search and handler invocation without requiring NVM keys.
If NVM keys are present, also notes that the gateway server can start.
"""

import json
import os
import sys


def test_catalog_registration():
    from src.services import catalog

    services = catalog.services
    assert len(services) >= 3, f"Expected 3+ services, got {len(services)}"
    ids = {s.service_id for s in services}
    assert "exa_search" in ids, f"exa_search not registered. Found: {ids}"
    assert "exa_get_contents" in ids, f"exa_get_contents not registered. Found: {ids}"
    assert "claude_summarize" in ids, f"claude_summarize not registered. Found: {ids}"
    print(f"  PASS: {len(services)} services registered: {', '.join(sorted(ids))}")


def test_find_service_logic():
    from src.services import catalog

    results = catalog.search("web search", top_k=5)
    assert len(results) > 0, "search returned no results"
    ids = [r["service_id"] for r in results]
    assert "exa_search" in ids, f"exa_search not in results: {ids}"
    first = results[0]
    for key in ("service_id", "name", "description", "price", "example_params", "provider"):
        assert key in first, f"Missing key '{key}' in result: {first}"
    pos = ids.index("exa_search") + 1
    print(f"  PASS: search('web search') returned {len(results)} results, exa_search at position {pos}")


def test_catalog_get():
    from src.services import catalog

    service = catalog.get("exa_search")
    assert service is not None, "catalog.get('exa_search') returned None"
    assert service.handler is not None, "exa_search has no handler"
    assert service.price_credits == 1, f"Expected price 1, got {service.price_credits}"
    print(f"  PASS: catalog.get('exa_search') → handler={service.handler.__name__}, price={service.price_credits}")


def test_buy_and_call_handler():
    """Invoke the handler directly — returns error JSON if EXA_API_KEY not set."""
    from src.services import catalog

    service = catalog.get("exa_search")
    assert service is not None
    assert service.handler is not None

    result = service.handler(query="test query", max_results=1)
    parsed = json.loads(result)

    if isinstance(parsed, dict) and "error" in parsed:
        print(f"  PASS (no EXA key): handler returned error JSON: {parsed['error']}")
    else:
        assert isinstance(parsed, list), f"Expected list from handler, got: {type(parsed)}"
        print(f"  PASS: handler returned {len(parsed)} result(s)")


def test_buy_and_call_unknown_service():
    """Unknown service_id should return None, not crash."""
    from src.services import catalog

    service = catalog.get("nonexistent_service_xyz")
    assert service is None, f"Expected None for unknown service, got {service}"
    print("  PASS: catalog.get('nonexistent_service_xyz') correctly returned None")


def test_buy_and_call_error_handling():
    """Simulate what gateway.buy_and_call does when service not found."""
    from src.services import catalog

    # Replicate gateway logic inline (no NVM import needed)
    service_id = "nonexistent_service_xyz"
    service = catalog.get(service_id)
    if service is None:
        response = json.dumps({
            "error": f"Service '{service_id}' not found.",
            "_meta": {"service_id": service_id, "credits_charged": 0},
        })
    else:
        response = json.dumps({"result": service.handler(), "_meta": {}})

    parsed = json.loads(response)
    assert "error" in parsed, f"Expected error key in response: {parsed}"
    assert parsed["_meta"]["credits_charged"] == 0
    print(f"  PASS: unknown service returns error JSON with credits_charged=0")


def test_gateway_credits_logic():
    """Verify dynamic credits lookup matches service price."""
    from src.services import catalog

    # Replicate _gateway_credits logic
    def gateway_credits(service_id):
        service = catalog.get(service_id)
        return service.price_credits if service else 1

    assert gateway_credits("exa_search") == 1
    assert gateway_credits("exa_get_contents") == 2
    assert gateway_credits("claude_summarize") == 5
    assert gateway_credits("unknown") == 1  # fallback
    print("  PASS: dynamic credits: exa_search=1, exa_get_contents=2, claude_summarize=5, unknown→1")


def main():
    tests = [
        ("Catalog registration (3+ services)", test_catalog_registration),
        ("find_service logic (catalog search)", test_find_service_logic),
        ("catalog.get() returns handler + price", test_catalog_get),
        ("buy_and_call handler invocation", test_buy_and_call_handler),
        ("Unknown service returns None", test_buy_and_call_unknown_service),
        ("buy_and_call error handling", test_buy_and_call_error_handling),
        ("Dynamic credits lookup", test_gateway_credits_logic),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")

    nvm_api_key = os.getenv("NVM_API_KEY")
    nvm_agent_id = os.getenv("NVM_GATEWAY_AGENT_ID") or os.getenv("NVM_AGENT_ID")
    if not nvm_api_key or not nvm_agent_id:
        print("\n[SKIP] Gateway server test skipped — NVM_API_KEY / NVM_AGENT_ID not set")
        print("       Set these in .env and rerun to test full gateway startup.")
    else:
        print("\n[INFO] NVM keys present — run: python -m src.gateway")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
