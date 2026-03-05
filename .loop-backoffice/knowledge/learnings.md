# Back-Office Learnings

## 2026-03-05

- Initial portfolio has 3 manually-added services (exa_search, exa_get_contents, claude_summarize). All zero discovery/wrapping cost.
- exa_search is the most popular service (7 calls). claude_summarize has 1 call at higher price (5 credits).
- exa_get_contents has zero usage — may need better discoverability or may just be niche.
- Available API keys: Exa, Anthropic, ZeroClick. Other keys require escalation to Mattie.
- Budget is healthy at 93 credits. Can afford multiple scout + wrap cycles.
- **Bug fixed:** `lib/actions.py` `init_paths()` was hardcoded to `.loop` — didn't respect `LOOP_DIR` env var. This caused all daemon dispatch/merge/move-to-eval actions to fail silently in the `.loop-backoffice` worktree. Fixed by adding `os.environ.get("LOOP_DIR")` fallback (same pattern as `assess.py`).
- **Bug fixed:** `lib/actions.py` `read_config()` didn't handle inline comments in config.sh. Line `GIT_MAIN_BRANCH="backoffice"  # comment` parsed as full string including comment. Fixed with proper quoted-value parsing.
- **Bug fixed:** Branch naming `backoffice/NNN-slug` conflicts with existing `backoffice` branch (git ref namespace). Changed to `bo/NNN-slug` prefix.
- **Infrastructure note:** Daemon must be restarted manually after these fixes. PID file may be stale.
