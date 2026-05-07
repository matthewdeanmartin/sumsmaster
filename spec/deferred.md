# Deferred work

Phase 0 (this commit) only proves the *trick-coverage* premise. Everything
below is intentionally postponed — capture here, not in code.

## Phase 0 result

- 43 tricks defined across +, −, ×, ÷.
- Coverage on the elementary fact space (`+0..12`, `−0..20`, `×0..12`,
  `÷ inverse of 1..12 grid`):
  - addition: 100%
  - subtraction: 97.4% (6 stragglers, all teen-minus-teen with small results)
  - multiplication: 100%
  - division: 100%
  - **overall: 99.2% (707 / 713 facts)**
- Conclusion: the "tricks-as-the-unit-of-mastery" thesis is viable. Building
  the spaced-repetition product around it is justified.

Run `python -m sumsmaster coverage` to reproduce, `python -m sumsmaster tricks`
to dump the taxonomy.

## Deferred to Milestone 1 (PoC)

These were in the spec.md "Phase 0 deliverables" list but are out of scope
until we have a working SR loop.

- **Problem-generation rules per trick.** Today we only *detect* trick
  applicability on enumerated facts. We don't yet generate fresh examples
  from a trick family. Needs: a generator interface alongside each `Trick`
  (e.g. `sample_problem(rng, difficulty) -> Problem`) and a way to vary
  difficulty within a trick.
- **Initial learner-state model.** No `SkillState` yet. Phase 1 needs
  per-trick `(attempts, correct, ease, interval, due_at, mastery_level)`.
- **Definition of "mastered" per trick.** Currently undefined. Likely a
  function of recent accuracy + spacing achieved + breadth of examples
  seen within the trick family.
- **SQLAlchemy + Alembic.** No storage layer at all in phase 0. The spec
  recommends SQLAlchemy 2.x from day one — defer to phase 1 when we have
  state worth persisting.
- **Answer-checking infrastructure.** Today `Problem.answer` exists but
  there's no review/grading loop.
- **CLI practice loop.** `sumsmaster coverage` reports; nothing yet quizzes.

## Deferred trick-taxonomy work

Catalogued during phase 0 — useful follow-ups but not needed to validate the
core idea.

- **Multi-trick "preferred path" ranking.** Many facts match 3+ tricks
  (e.g. `4×8` matches double-and-half, ×4-as-double-double, distributive
  split, near-doubles-of-products). For teaching, we want a *primary*
  trick. Needs a per-trick difficulty/elegance score and a tiebreaker.
- **Diagnostic tricks for wrong-answer analysis.** spec.md §4 wants
  mistakes to update the learner model based on *which* trick was likely
  attempted. We have detectors for trick applicability but no model of
  "what failure mode would produce answer X?".
- **Larger-domain tricks.** Things like `25×n = n×100÷4`, `near-50
  multiplication`, `squaring teens (n² = (n-10)·(n+10) + 10²-100 + …)`,
  divisibility rules for 3/9/11. Out of scope for the 12×12 grid; relevant
  if we extend to 2-digit × 2-digit.
- **Subtraction stragglers.** 17−13, 18−13, 18−14, 19−13, 19−14, 19−15.
  Easiest fix: extend `count up (small gap)` from window=3 to window=6,
  or add a `teen − teen` trick. Held back deliberately so we don't paper
  over the gap in the report.
- **Negative-result subtraction.** Currently the subtraction domain only
  generates `a ≥ b`. When we expand, we need negative-result tricks
  (e.g. `a − b = -(b − a)`).
- **Non-integer division.** Phase 0 only generates clean inverse-of-mul
  facts. Real division curriculum will need remainders, decimals, fractions.

## Deferred infrastructure

- **Trick prerequisites graph.** spec.md mentions per-trick prerequisites.
  Today every trick stands alone. Phase 1+ needs ordering ("you can only
  drill `add 9 as 10−1` once `add 10` is mastered").
- **Learner-facing explanations and hints.** `Trick.explanation` is a
  one-liner aimed at the developer. Real teaching needs worked examples,
  common mistakes, and possibly visualisations.
- **Curriculum schedule.** Which tricks to introduce first, and in what
  order, for a brand-new learner.
- **Persistence, sync, accounts, billing, leaderboards.** All milestones
  ≥2 from spec.md.

## Open questions to revisit before phase 1

1. Should a `Trick` own both *detect* and *generate*, or should those be
   separate registries? (Today only detect exists.)
2. Are detectors for "trick *could* apply" the right thing, or do we want
   "trick is the *easiest* path"? Currently a mix — see e.g. the
   `MUL_NEAR_TEN` vs `MUL_NINE_FINGER` overlap, kept on purpose for
   diagnostic visibility.
3. How do we handle commutative duplicates (`3×7` vs `7×3`) in the
   learner model? Same fact or two? Probably one — needs a canonical
   key on `Problem`.
