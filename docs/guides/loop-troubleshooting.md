# Simple-Loop Daemon Troubleshooting

Field notes from running the simple-loop daemon overnight (March 5-6, 2026). These are hard-won lessons.

## #1: You cannot edit tracked files while the daemon runs

**Symptom:** You edit a file, commit succeeds, but the file reverts. Or `git add` shows nothing to stage. Or the Edit/Write tool says "success" but the change doesn't stick.

**Cause:** The daemon and your session share the same git working directory. Every tick (~30s), the daemon runs `git checkout main && git pull`, which resets all tracked files to the remote state. Your uncommitted changes get wiped silently.

**Even pausing doesn't help.** `./bin/loop pause` writes a signal file, but the daemon's git cleanup still runs on every tick.

**Fix:** `./bin/loop stop` — fully stop the daemon, make your changes, commit, push, then `./bin/loop start`. This is the only reliable way to edit tracked files.

**Future fix:** Worktree support in the daemon, so it operates in an isolated copy and never touches main's working tree.

## #2: Merge conflicts on progress.json and hackathon-diary.md

**Symptom:** Every merge fails with conflicts on the same two files. Loop spins retrying every 30s.

**Cause:** Both the worker branch and main write to these files independently:
- `progress.json` — worker writes progress on branch, conductor writes different progress on main
- `hackathon-diary.md` — worker adds a diary entry on branch, conductor adds a different entry on main

**Fix deployed in `lib/actions.py`:**
- `progress.json`: auto-resolve with `--theirs` (take branch version, it's the latest brief)
- `hackathon-diary.md`: strip conflict markers, keep both sides (both entries are worth keeping)
- Any other conflicted file: abort merge and raise error (needs human attention)

## #3: Stuck merge state blocks everything

**Symptom:** `needs merge` errors on every git operation. Cannot checkout branches. Cannot stash. Loop spins forever.

**Cause:** A merge was attempted, conflicted, but never resolved or aborted. Git is in a "merging" state that blocks all other operations. `git stash` won't work. `git checkout` won't work.

**Fix deployed in `lib/daemon.sh` and `lib/actions.py`:**
- `git merge --abort` runs before every merge attempt (clears stuck state from previous failures)
- `git merge --abort` runs at worker start before checkout
- `git merge --abort` runs in the tick cleanup before switching to main

**Manual fix:** `git merge --abort && git checkout main`

## #4: "Branch already exists" on dispatch

**Symptom:** `fatal: a branch named 'brief-XXX' already exists` — dispatch fails and retries forever.

**Cause:** A previous dispatch failed mid-way, leaving a stale local branch. The daemon tries `git checkout -b` which fails if the branch exists.

**Fix deployed in `lib/actions.py`:** `git branch -D <branch>` (with `check=False`) before `git checkout -b`. Deletes the stale branch so creation succeeds.

**Manual fix:** `git branch -D brief-XXX-whatever`

## #5: Push rejected (non-fast-forward)

**Symptom:** `git push` fails with "remote contains work that you do not have locally."

**Cause:** The daemon or another session pushed to main while you were working. Common when both you and the daemon are active.

**Fix:** `git pull --rebase origin main && git push origin main`

## General advice

- **Always stop the loop before editing code.** `./bin/loop stop`, edit, commit, push, `./bin/loop start`.
- **Check `./bin/loop status`** to see what the daemon is doing before intervening.
- **If something is stuck**, the nuclear option is: `./bin/loop stop && git merge --abort; git checkout main && git reset --hard origin/main && ./bin/loop start`
- **The daemon log** (`./bin/loop logs -f`) shows exactly what's happening on each tick.
- **Worktree support** would solve most of these problems. It's the right long-term fix.
