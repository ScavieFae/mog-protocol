"""Tests for Trace, VaultLayer, BlockerLayer, and graceful degradation."""

import os
import sys
import tempfile
import threading
import unittest


class TestTrace(unittest.TestCase):
    def setUp(self):
        from src.toolkit import Trace
        self.Trace = Trace

    def test_log_and_steps(self):
        t = self.Trace("test op")
        t.log("browse", "navigate(x)", "ok title='Home'")
        self.assertEqual(len(t.steps), 1)
        self.assertIn("browse:navigate(x)", t.steps[0])

    def test_result_truncated_at_80(self):
        t = self.Trace()
        long_result = "x" * 200
        t.log("layer", "action", long_result)
        # The stored step is "layer:action -> {result[:80]}"
        # Result portion should be max 80 chars
        step = t.steps[0]
        result_part = step.split(" -> ", 1)[1]
        self.assertEqual(len(result_part), 80)

    def test_summary_caps_at_20(self):
        t = self.Trace()
        for i in range(25):
            t.log("layer", f"action{i}", "ok")
        self.assertEqual(len(t.steps), 25)
        self.assertEqual(len(t.summary()), 20)
        # Summary returns last 20
        self.assertIn("action24", t.summary()[-1])
        self.assertIn("action5", t.summary()[0])

    def test_to_dict(self):
        t = self.Trace("my operation")
        t.log("vault", "store(key)", "ok")
        d = t.to_dict()
        self.assertEqual(d["operation"], "my operation")
        self.assertEqual(d["step_count"], 1)
        self.assertIn("steps", d)
        self.assertIn("started_at", d)


class TestTraceWithBlocker(unittest.TestCase):
    def test_trace_stored_on_blocker_report(self):
        from src.toolkit import Trace, BlockerLayer
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            bl = BlockerLayer(path=path)
            t = Trace("test eval")
            t.log("browse", "navigate(signup)", "ok title='Signup'")
            t.log("browse", "fill_form(email)", "ok")
            t.log("browse", "click(Submit)", "FAIL captcha detected")
            report_id = bl.report(
                service_id="test_svc",
                blocker_type="captcha",
                description="CAPTCHA on signup",
                trace=t,
                recommendation="ESCALATE",
                opportunity_value=7,
            )
            reports = bl.get_recent()
            self.assertEqual(len(reports), 1)
            r = reports[0]
            self.assertEqual(r["id"], report_id)
            self.assertIsNotNone(r["trace"])
            self.assertEqual(r["trace"]["operation"], "test eval")
            self.assertEqual(r["trace"]["step_count"], 3)
            self.assertEqual(len(r["trace"]["steps"]), 3)
        finally:
            os.unlink(path)


class TestVaultLayer(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmpfile.close()
        os.unlink(self.tmpfile.name)  # Start fresh (file won't exist)
        from src.toolkit import VaultLayer
        self.vault = VaultLayer(path=self.tmpfile.name)

    def tearDown(self):
        if os.path.exists(self.tmpfile.name):
            os.unlink(self.tmpfile.name)

    def test_store_and_get(self):
        self.vault.store("mykey", "myvalue", service_id="svc1", source="test")
        self.assertEqual(self.vault.get("mykey"), "myvalue")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.vault.get("does_not_exist"))

    def test_overwrite(self):
        self.vault.store("key", "old")
        self.vault.store("key", "new")
        self.assertEqual(self.vault.get("key"), "new")

    def test_list_keys_no_values(self):
        self.vault.store("k1", "secret1", service_id="svc1")
        self.vault.store("k2", "secret2", service_id="svc2")
        keys = self.vault.list_keys()
        self.assertEqual(len(keys), 2)
        key_names = {k["key_name"] for k in keys}
        self.assertIn("k1", key_names)
        self.assertIn("k2", key_names)
        # Values must NOT be exposed
        for k in keys:
            self.assertNotIn("value", k)

    def test_delete(self):
        self.vault.store("del_key", "val")
        self.assertTrue(self.vault.delete("del_key"))
        self.assertIsNone(self.vault.get("del_key"))

    def test_delete_missing_returns_false(self):
        self.assertFalse(self.vault.delete("nonexistent"))

    def test_persistence_round_trip(self):
        from src.toolkit import VaultLayer
        self.vault.store("persist_key", "persist_val", service_id="svc")
        # New instance, same path
        vault2 = VaultLayer(path=self.tmpfile.name)
        self.assertEqual(vault2.get("persist_key"), "persist_val")

    def test_thread_safety(self):
        errors = []

        def worker(n):
            try:
                self.vault.store(f"key_{n}", f"val_{n}")
                assert self.vault.get(f"key_{n}") == f"val_{n}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])


class TestBlockerLayer(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmpfile.close()
        os.unlink(self.tmpfile.name)
        from src.toolkit import BlockerLayer
        self.bl = BlockerLayer(path=self.tmpfile.name)

    def tearDown(self):
        if os.path.exists(self.tmpfile.name):
            os.unlink(self.tmpfile.name)

    def test_report_returns_id(self):
        report_id = self.bl.report("svc", "captcha", "blocked by captcha")
        self.assertTrue(report_id.startswith("blk-"))

    def test_get_recent(self):
        self.bl.report("svc1", "captcha", "a")
        self.bl.report("svc2", "paywall", "b")
        recent = self.bl.get_recent()
        self.assertEqual(len(recent), 2)
        # Newest first
        self.assertEqual(recent[0]["service_id"], "svc2")

    def test_get_recent_limit(self):
        for i in range(5):
            self.bl.report(f"svc{i}", "captcha", "x")
        self.assertEqual(len(self.bl.get_recent(limit=3)), 3)

    def test_get_by_type(self):
        self.bl.report("svc1", "captcha", "a")
        self.bl.report("svc2", "paywall", "b")
        self.bl.report("svc3", "captcha", "c")
        captchas = self.bl.get_by_type("captcha")
        self.assertEqual(len(captchas), 2)
        for r in captchas:
            self.assertEqual(r["blocker_type"], "captcha")

    def test_get_escalations(self):
        self.bl.report("svc1", "captcha", "a", recommendation="ESCALATE")
        self.bl.report("svc2", "paywall", "b", recommendation="SKIP")
        self.bl.report("svc3", "other", "c", recommendation="ESCALATE")
        esc = self.bl.get_escalations()
        self.assertEqual(len(esc), 2)

    def test_report_no_trace(self):
        report_id = self.bl.report("svc", "other", "desc")
        reports = self.bl.get_recent()
        self.assertIsNone(reports[0]["trace"])


class TestGracefulDegradation(unittest.TestCase):
    """Verify all methods return safe defaults when API keys are missing."""

    def setUp(self):
        # Temporarily remove API keys
        self._bb_key = os.environ.pop("BROWSERBASE_API_KEY", None)
        self._bb_proj = os.environ.pop("BROWSERBASE_PROJECT_ID", None)
        self._am_key = os.environ.pop("AGENTMAIL_API_KEY", None)
        # Re-import to get fresh instances without keys
        import importlib
        import src.toolkit as tk
        importlib.reload(tk)
        from src.toolkit import BrowseLayer, EmailLayer
        self.browse = BrowseLayer()
        self.email = EmailLayer()

    def tearDown(self):
        if self._bb_key:
            os.environ["BROWSERBASE_API_KEY"] = self._bb_key
        if self._bb_proj:
            os.environ["BROWSERBASE_PROJECT_ID"] = self._bb_proj
        if self._am_key:
            os.environ["AGENTMAIL_API_KEY"] = self._am_key

    def test_browse_create_session_no_key(self):
        result = self.browse.create_session()
        self.assertIn("error", result)
        self.assertIn("BROWSERBASE_API_KEY", result["error"])

    def test_browse_navigate_no_key(self):
        result = self.browse.navigate("fake-session", "https://example.com")
        self.assertIn("error", result)

    def test_browse_fill_form_no_key(self):
        result = self.browse.fill_form("fake-session", {"email": "x"})
        self.assertFalse(result)

    def test_browse_click_no_key(self):
        result = self.browse.click("fake-session", "Submit")
        self.assertFalse(result)

    def test_browse_get_text_no_key(self):
        result = self.browse.get_text("fake-session")
        self.assertEqual(result, "")

    def test_email_create_inbox_no_key(self):
        result = self.email.create_inbox("test")
        self.assertIn("error", result)
        self.assertIn("AGENTMAIL_API_KEY", result["error"])

    def test_email_send_no_key(self):
        result = self.email.send("inbox", "to@example.com", "sub", "body")
        self.assertFalse(result)

    def test_email_check_inbox_no_key(self):
        result = self.email.check_inbox("inbox")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
