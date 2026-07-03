# Tkinter GUI — free, self-hosted (pipx) edition

## Goal

Give the free, locally installed (`pipx install sumsmaster`) edition a graphical
front end that surfaces everything the package can already do, plus the
minimum learner-facing loop from Milestone 1:

* browse the trick taxonomy,
* view the coverage report,
* practice generated, trick-tagged problems,
* track per-trick progress (attempts, accuracy, streak, mastery),
* pause a session and resume it later,
* basic **unauthenticated local profiles** — use the built-in `default`
  profile or create a named one and pick a **plan**.

This is the freemium split: the free tier is fully local (JSON files under the
user's home directory), no accounts, no network. Paid cloud sync, leaderboards
etc. remain out of scope.

## Non-goals

* No authentication, passwords, or remote storage.
* No SQLite/SQLAlchemy yet — profile files are small JSON documents; the
  storage layer is isolated behind `ProfileStore` so it can be swapped later.
* No third-party dependencies. `tkinter` ships with CPython; everything else
  is stdlib. (pipx users on Debian/Ubuntu may need `python3-tk` — the CLI
  prints a friendly error if tkinter is missing.)
* No mistake diagnosis (roadmap §4) — a wrong answer just records a miss.

## Entry points

* `sumsmaster gui` — new CLI subcommand.
* `sumsmaster-gui` — dedicated `[project.gui-scripts]` entry so Windows users
  get a no-console launcher.

## Package layout

```text
sumsmaster/gui/
  __init__.py     # launch() — import guard for tkinter, builds and runs App
  store.py        # Profile, TrickProgress, SessionState, ProfileStore (JSON)
  plans.py        # Plan definitions derived from the trick registry
  practice.py     # PracticeSession engine: generation, checking, progress
  app.py          # Tk application: screens, navigation, event wiring
```

`store.py`, `plans.py`, and `practice.py` are pure logic (no tkinter import)
so they are unit-testable headless.

## Profiles

* Stored one file per profile at `~/.sumsmaster/profiles/<slug>.json`
  (override root with `SUMSMASTER_HOME` for tests/self-hosters).
* A `default` profile is created automatically on first launch with the
  `everything` plan, so the app is usable with zero setup.
* Creating a profile: pick a display name (slugified for the filename) and a
  plan. Names are unique by slug; no password ("unauthenticated" by design).
* The last-used profile slug is remembered in `~/.sumsmaster/settings.json`
  and preselected on next launch.

Profile document (versioned for forward migration):

```json
{
  "version": 1,
  "name": "Maya",
  "plan": "times-tables",
  "created_at": "2026-07-03T12:00:00+00:00",
  "progress": {
    "multiply by 5": {"attempts": 9, "correct": 8, "streak": 4, "last_practiced": "..."}
  },
  "session": { ... SessionState or null ... }
}
```

## Plans

A plan is a named, ordered subset of tricks with a problem domain — the free
tier's version of "pick a course". Defined in code from `ALL_TRICKS`:

| id | name | contents |
|----|------|----------|
| `everything` | Everything | all tricks, all four domains |
| `addition-foundations` | Addition Foundations | addition tricks |
| `subtraction-strategies` | Subtraction Strategies | subtraction tricks |
| `times-tables` | Times-Table Tricks | multiplication tricks |
| `division-basics` | Division Basics | division tricks |

Plans validate at import time: every trick referenced must exist in the
registry (guards against renames).

## Practice engine

* Problems are drawn from the same phase-0 domains used by
  `sumsmaster.coverage` (addition 0–12, subtraction 0–20 non-negative,
  multiplication 0–12, division inverse grid), filtered to facts where the
  target trick fires. This keeps GUI problems consistent with the analyzed
  fact space.
* Trick selection is mastery-weighted: unmastered tricks with the fewest
  correct answers are preferred; mastered tricks still appear occasionally
  (light review), matching the "stop hammering mastered patterns" thesis.
* A session is a fixed-length queue (default 10 problems). Each answer
  records attempt/correct/streak on the trick and shows the trick's name and
  explanation as feedback (teach the strategy, not just the fact).
* **Mastery**: a trick is mastered when `streak >= 5` (roadmap's "definition
  of mastered" placeholder — tune later).

## Resume

* After every answer the session state (remaining problem queue as
  `(a, b, op, trick)` tuples, position, hits/misses) is written into the
  profile JSON.
* Quitting mid-session (window close or Back) keeps the saved state; the
  dashboard shows a **Resume session (k of n)** button when one exists.
  Finishing or abandoning a session clears it.

## Screens

```text
ProfileScreen   pick existing profile / create (name + plan) / delete
DashboardScreen greeting, plan, mastery summary bar, per-trick progress
                table (attempts, accuracy, streak, mastered ✓),
                [Start practice] [Resume session] [Browse tricks]
                [Coverage report] [Switch profile] [Change plan]
PracticeScreen  problem prompt, answer entry (Enter submits), feedback with
                trick explanation, progress "k / n", [End session]
TricksScreen    read-only tree of tricks grouped by operation with
                explanations (the `tricks` CLI feature, graphically)
CoverageScreen  scrollable monospace text of coverage.default_report()
                (computed in a background thread to keep the UI live)
```

One `Tk` root; screens are `ttk.Frame`s swapped in a container (simple
router, no extra windows).

## Testing

* Unit tests for `store` (round-trip, default profile, resume payload,
  corrupt-file tolerance), `plans` (registry integrity), and `practice`
  (generation matches trick, answer checking, mastery/streak updates,
  session serialization) — all headless.
* GUI smoke test constructs the `App` only if `tkinter` can open a display,
  otherwise skips (CI-safe).
