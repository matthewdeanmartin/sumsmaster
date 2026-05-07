# Sumsmaster Roadmap

## Product thesis

**Sumsmaster** is a mental-math learning app that teaches arithmetic through reusable strategies, not brute-force memorization.

Unlike generic flashcard systems, Sumsmaster understands that many arithmetic facts belong to the same underlying trick. Once a learner demonstrates mastery of a trick, the app should reduce or stop showing equivalent problems that merely instantiate the same pattern.

Example:

> If the learner understands `n × 10 = append a zero`, then `2 × 10`, `9 × 10`, and `47 × 10` should reinforce the same concept, not behave like unrelated facts.

The app combines:

* spaced repetition,
* trick-based problem classification,
* adaptive practice,
* local-first learning,
* optional paid cloud sync,
* leaderboards and social motivation,
* eventual multi-interface support.

---

# North Star

Help learners become fast and confident at mental arithmetic by mastering **generalizable tricks**.

The system should answer:

> “What mental-math strategy is this problem testing, and has the learner mastered that strategy?”

Not merely:

> “Has the learner memorized this exact equation?”

---

# Core learning model

## 1. Problems are generated, not manually listed

Sumsmaster should avoid static decks like:

```text
2 × 10
3 × 10
4 × 10
...
```

Instead, it should define **problem families** and generate examples from them.

Example family:

```text
Multiply by 10
a × 10
10 × a
```

With generated examples:

```text
7 × 10
10 × 23
481 × 10
```

## 2. Each problem maps to one or more tricks

A problem may be solvable by multiple strategies.

Example:

```text
25 × 16
```

Possible tricks:

```text
25 × n = n × 100 ÷ 4
16 = 2⁴
quartering / doubling
```

The app should eventually support multiple valid trick paths, but the early versions can assign one primary intended trick per generated problem.

## 3. Spaced repetition tracks tricks, not only answers

The learner should have progress on:

* exact problem instances,
* problem families,
* tricks,
* operations,
* difficulty bands.

This allows the app to infer:

> “You do not need ten more `×10` cards. You need more practice applying compensation in subtraction.”

## 4. Mistakes should diagnose the failed skill

A wrong answer is not just wrong. It should update the learner model.

Example:

```text
98 + 37
```

Intended trick:

```text
100 + 37 - 2
```

If the learner answers `135`, they likely know the trick.

If they answer `125`, the issue may be compensation direction.

The app does not need perfect diagnosis at first, but the architecture should leave room for this.

---

# Product roadmap

## Milestone 0: Concept definition

Goal: define the learning grammar before building too much software.

### Outcomes

Create a small but rigorous mental-math taxonomy:

```text
Operations:
- addition
- subtraction
- multiplication
- division

Trick categories:
- identity / zero / one rules
- powers of 10
- doubling and halving
- near-ten compensation
- near-hundred compensation
- commutativity
- distributive decomposition
- complements
- checksum / sanity-check tricks
- divisibility tricks
- factorization tricks
```

### Example initial tricks

```text
Addition:
- add 10
- add 9 as add 10 minus 1
- add 11 as add 10 plus 1
- make 10
- make 100
- reorder terms

Subtraction:
- subtract 10
- subtract 9 as subtract 10 plus 1
- subtract near multiples of 10
- count up difference
- borrow-friendly decomposition

Multiplication:
- multiply by 0
- multiply by 1
- multiply by 2
- multiply by 5
- multiply by 10
- multiply by 11
- use commutativity
- double-and-half
- distribute over addition
- distribute over subtraction

Division:
- divide by 1
- divide by 2
- divide by 5
- divide by 10
- inverse multiplication facts
- simplify by common factors
```

### Deliverables

* Written taxonomy of initial tricks.
* Problem-generation rules for each trick.
* Initial learner-state model.
* Definition of what “mastered” means for a trick.

This is not yet a product milestone. It is the learning-design foundation.

---

# Milestone 1: Proof of Concept

Goal: prove that trick-aware spaced repetition feels meaningfully better than naive flashcards.

This can be a terminal app or simple local Python UI.

## Scope

The PoC should support:

```text
- local user profile
- generated arithmetic problems
- trick-tagged problems
- answer checking
- basic spaced repetition
- mastery tracking per trick
- simple review loop
- SQLite storage
```

## Recommended implementation shape

Python backend with clean domain separation:

```text
sumsmaster/
  domain/
    problems.py
    tricks.py
    scheduler.py
    learner_model.py
  storage/
    models.py
    repository.py
  app/
    cli.py
```

Use a real ORM from day one.

Recommended ORM:

```text
SQLAlchemy 2.x
```

Why:

* works with SQLite and Postgres,
* mature,
* supports migrations via Alembic,
* suitable for both local and server deployments,
* avoids locking the app into one framework.

Use:

```text
SQLite for PoC/local
Postgres for SaaS later
SQLAlchemy ORM
Alembic migrations
```

## Core entities

```text
User
Trick
ProblemTemplate
GeneratedProblem
Review
SkillState
```

In the PoC, `User` can just be a local profile, not real authentication.

## Scheduling model

Start simple.

Track per trick:

```text
- attempts
- correct attempts
- current interval
- ease score
- due date
- mastery level
```

The scheduler should choose problems based on due tricks, then generate fresh examples from those trick families.

Important distinction:

```text
Do not schedule only "7 × 10".
Schedule "multiply by 10", then generate a suitable example.
```

## Success criteria

The PoC succeeds if:

1. A learner can practice arithmetic locally.
2. Problems are generated from trick families.
3. Mastering one example reduces redundant exposure to equivalent examples.
4. The app can say things like:

```text
Strong:
- multiply by 10
- add 9
- double single-digit numbers

Needs work:
- subtract near 100
- divide by 5
```

---

# Milestone 2: Useful Local MVP

Goal: make Sumsmaster valuable as a self-contained personal learning tool.

This should be good enough that someone can install it, practice daily, and improve.

## Scope

The local MVP should include:

```text
- local account/profile
- SQLite database
- richer problem generation
- review sessions
- daily goals
- trick mastery dashboard
- mistake history
- import/export
- self-host-friendly architecture
```

## User experience

A basic local web app would be preferable here over CLI.

Recommended stack:

```text
Backend:
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

Frontend:
- simple server-rendered HTML at first, or
- lightweight React/Vue/Svelte if desired

Local database:
- SQLite
```

FastAPI is a good choice because it naturally supports future multiple UIs through a clean API.

## Core local features

### Practice session

User chooses:

```text
- review due tricks
- practice a specific operation
- practice weak areas
- learn new trick
- mixed session
```

### Trick explanation

Each trick should have:

```text
- name
- short explanation
- example
- generated practice problems
- optional hint
- common mistakes
```

Example:

```text
Trick: Multiply by 5

Mental method:
Multiply by 10, then halve.

Example:
24 × 5
= 24 × 10 ÷ 2
= 240 ÷ 2
= 120
```

### Mastery dashboard

Show progress by trick, not merely by total questions answered.

Example:

```text
Multiplication
- ×10: mastered
- ×5: learning
- ×11: new
- double-and-half: weak
```

### Local data ownership

Because self-hosting is part of the product direction, the local MVP should make data portable early.

Support:

```text
- export progress as JSON
- import progress from JSON
- backup SQLite database
```

## Success criteria

The local MVP succeeds if it is useful without a server.

A user should be able to:

```text
install it,
practice for 10 minutes a day,
see what tricks they are learning,
and retain progress locally.
```

---

# Milestone 3: Self-hostable Web App

Goal: prepare the architecture for public SaaS without yet requiring a hosted business.

This is the bridge between local MVP and paid cloud service.

## Scope

Add production-shaped web concerns:

```text
- FastAPI backend
- Postgres support
- Docker deployment
- environment-based config
- database migrations
- basic authentication
- multiple users
- admin tools
```

## Authentication

For a one-person shop, avoid maintaining complex enterprise auth.

Recommended approach:

```text
Managed auth for SaaS, simple auth for self-hosting.
```

Options:

### For self-hosting

Use simple email/password auth with:

```text
- secure password hashing
- password reset disabled or SMTP-configurable
- optional local-only mode
```

### For SaaS

Use a managed provider or simple external OAuth-friendly system.

Good candidates:

```text
- Auth0
- Clerk
- Supabase Auth
- WorkOS only if B2B/SSO later matters
```

Since the product is consumer-facing and solo-operated, avoid enterprise SSO initially.

A reasonable roadmap choice:

```text
Start with email/password + OAuth through a managed auth provider.
Add passkeys later.
Do not support enterprise SSO in early SaaS.
```

## Deployment

Self-hosting should support:

```text
docker compose up
```

With services:

```text
- app
- postgres
- optional redis
```

Redis can be deferred unless needed for background jobs or rate limiting.

## Success criteria

The self-hosted web app succeeds if:

```text
- multiple users can run it on their own server
- data can live in Postgres
- authentication works
- the API boundary is clean
- the same domain logic still powers everything
```

---

# Milestone 4: Web SaaS

Goal: launch the hosted version of Sumsmaster.

The paid version charges for server-side progress storage, syncing, and cloud convenience.

## Free vs paid model

### Free

```text
- use the app locally
- possibly limited anonymous web demo
- no persistent cloud sync, or limited progress storage
```

### Paid

```text
- cloud account
- server-side progress storage
- sync across devices
- backups
- leaderboard participation
- advanced analytics
```

The clean positioning:

> The learning engine is available locally. The paid product is hosted progress, sync, convenience, and social features.

## Stripe integration

Use Stripe Billing.

Support:

```text
- monthly subscription
- annual subscription
- customer portal
- webhook handling
- payment status syncing
```

Core Stripe events to handle:

```text
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
invoice.payment_failed
```

The app should store:

```text
User
Subscription
Plan
StripeCustomer
StripeSubscription
Entitlement
```

Avoid scattering payment checks throughout the codebase. Use a centralized entitlement service:

```text
can_sync_progress(user)
can_access_leaderboard(user)
can_use_cloud_storage(user)
```

## SaaS infrastructure

Minimum viable hosted stack:

```text
- FastAPI app
- Postgres
- object storage for backups/exports if needed
- hosted auth
- Stripe
- email provider
- logging
- error monitoring
```

Recommended services:

```text
Hosting:
- Fly.io
- Render
- Railway
- DigitalOcean App Platform
- AWS/GCP/Azure only if needed later

Database:
- managed Postgres

Email:
- Postmark
- Resend
- Mailgun

Monitoring:
- Sentry
- basic structured logs
```

## Leaderboard

Leaderboards should avoid rewarding meaningless grinding.

Track meaningful metrics:

```text
- daily streak
- weekly consistency
- tricks mastered
- accuracy at difficulty level
- speed improvements
```

Avoid pure “most questions answered” as the primary ranking because it encourages spammy behavior.

Possible leaderboard categories:

```text
- weekly improvement
- longest current streak
- tricks mastered this month
- fastest accurate session
- division specialist
- multiplication specialist
```

## Success criteria

Web SaaS succeeds if:

```text
- users can register
- users can subscribe
- progress is saved server-side
- web practice works reliably
- local/self-hosted architecture remains intact
- leaderboard exists without compromising learning quality
```

---

# Milestone 5: Multi-UI SaaS

Goal: make Sumsmaster available through multiple clients while preserving one learning engine.

Supported interfaces may include:

```text
- public web app
- mobile web
- native iOS
- native Android
- desktop wrapper
- CLI for power users
```

## Architecture principle

The learning engine must remain UI-independent.

The core system should expose APIs like:

```text
GET /session/next
POST /session/answer
GET /tricks
GET /progress
POST /sync
GET /leaderboard
```

The UI should not decide what the learner needs next. The backend/domain layer should.

## Client types

### Public website

Primary interface.

Features:

```text
- onboarding
- practice
- progress dashboard
- billing
- account management
```

### Mobile web

Should come before native apps.

Mental math practice is well-suited to a responsive web UI.

### Native mobile apps

Later, if there is traction.

Native apps can add:

```text
- offline sessions
- push reminders
- app-store presence
- smoother daily habit loops
```

### Offline-first clients

Important long-term idea:

```text
Practice should work offline.
Sync should reconcile later.
```

This requires careful data modeling:

```text
- local review logs
- server reconciliation
- idempotent sync events
- conflict-safe progress updates
```

## Success criteria

Multi-UI SaaS succeeds if:

```text
- multiple clients use the same API
- progress sync works across devices
- offline practice is possible
- mobile experience feels native enough
- the learning engine remains shared
```

---

# Technical roadmap summary

## Early technology choices

Recommended from day one:

```text
Language:
- Python

Backend:
- FastAPI

ORM:
- SQLAlchemy 2.x

Migrations:
- Alembic

Local DB:
- SQLite

Hosted DB:
- Postgres

Validation:
- Pydantic

Payments:
- Stripe Billing

Auth:
- managed auth for SaaS
- simple local auth for self-host/self-contained use

Testing:
- pytest

Packaging:
- Docker
- docker compose
```

## Core architecture

```text
Domain layer:
- tricks
- problem generation
- answer checking
- spaced repetition
- learner model

Application layer:
- sessions
- progress
- user accounts
- billing
- leaderboard

Infrastructure layer:
- SQLAlchemy repositories
- auth provider integration
- Stripe integration
- email
- deployment config

Interface layer:
- CLI
- web UI
- public API
- future mobile clients
```

The most important early rule:

> Do not let UI code own learning logic.

---

# Data model direction

Initial conceptual tables:

```text
users
tricks
problem_templates
generated_problems
reviews
skill_states
sessions
subscriptions
leaderboard_entries
```

Later additions:

```text
devices
sync_events
achievements
daily_goals
streaks
explanations
mistake_patterns
```

The most important table is probably not `problems`.

It is:

```text
skill_states
```

Because Sumsmaster is about tracking mastery of reusable arithmetic strategies.

---

# Learning roadmap

Start with a small, high-quality curriculum rather than a huge one.

## Initial curriculum

### Addition

```text
+0
+1
+2
+10
+9
+11
make 10
make 100
near-ten addition
near-hundred addition
```

### Subtraction

```text
-0
-1
-2
-10
-9
-11
subtract by compensation
count-up subtraction
near-ten subtraction
near-hundred subtraction
```

### Multiplication

```text
×0
×1
×2
×5
×10
×11
commutativity
doubling
double-and-half
distributive split
near-ten multiplication
```

### Division

```text
÷1
÷2
÷5
÷10
inverse multiplication
halve repeatedly
simplify before dividing
divisibility checks
```

Do not begin with every possible arithmetic fact. Begin with tricks that create the strongest “aha” effect.

---

# Main product risks

## Risk 1: The trick taxonomy becomes messy

Mitigation:

Start small. Every trick should have:

```text
- name
- explanation
- generator
- answer checker
- difficulty range
- prerequisites
```

## Risk 2: Spaced repetition over tricks is harder than cards

Mitigation:

Start with a simple scheduler and improve later.

The first version only needs to avoid obvious waste, such as over-drilling `×10`.

## Risk 3: Users may still want raw fact fluency

Mitigation:

Support both:

```text
- trick mastery
- fact fluency
```

But make trick mastery the distinctive feature.

## Risk 4: Leaderboards incentivize bad behavior

Mitigation:

Rank consistency, improvement, and mastery instead of raw volume.

## Risk 5: SaaS complexity overwhelms the learning product

Mitigation:

Keep local MVP genuinely useful before adding billing, cloud sync, and social systems.

---

# Recommended milestone order

## 1. Concept foundation

Define the trick taxonomy, generated problem format, and learner model.

## 2. PoC

Build a local Python practice loop that proves trick-aware scheduling.

## 3. Useful local MVP

Make a real local app with SQLite, dashboard, explanations, and progress.

## 4. Self-hosted web app

Add FastAPI, Postgres, Docker, auth, and multi-user support.

## 5. Web SaaS

Add hosted accounts, Stripe, cloud progress, and leaderboards.

## 6. Multi-UI SaaS

Add mobile-friendly clients, API hardening, sync, and eventually native apps.

---

# Guiding principle

Sumsmaster should not ask:

> “Which arithmetic facts has the user memorized?”

It should ask:

> “Which mental-math moves has the user internalized, and which problems will best strengthen the next move?”
