> ## ⚠️ Superseded mid-flight — only part of it was built
>
> **Written 26 August 2026, obsolete within a day.** It specified paste-a-list
> curriculum entry and per-unit pacing rhythms alongside the week planner. The
> owner then asked for units and importing to go entirely, so items 1 and 2 were
> never built — they were the same mistake one size smaller.
>
> Item 3, the week planner, was built and is the app's main screen. The reasoning
> in it about the weekly loop, pinned dates and surfacing the backlog to an adult
> all still holds.
>
> **What is true now:** `docs/BUILD_LOG.md`.

---

# Phase 3 Implementation Brief — The Weekly Loop

**For:** Claude Code, working in the `flokus-academy` repo
**Branch:** `feat/phase-3-weekly-loop`
**Written:** 2026-08-26, after the Tuttle Twins load
**Supersedes:** the Phase 3 described in the review doc §9 ("protect the student experience"). Most of that survives, reframed — see *Why this phase changed shape*.

---

## Why this phase changed shape

The importer was designed around a **migration**: 272 legacy lessons out of V1 and into V2 in one pass. That is a one-time problem, and it is now solved — Tuttle Twins went in cleanly.

But the teacher's actual life is a **weekly loop**:

```
plan offline  →  add a unit when it's ready  →  space it out
      →  check the week ahead on Sunday  →  repeat
```

Phase 2 handed him the migration's ceremony — build a workbook, export a sheet, adjust statuses, import a subject — as his everyday workflow. It is too heavy for the loop, and the loop is what he does fifty times a year. This phase builds the loop.

**What survives unchanged:** the domain model, staged-vs-released (wanted *more* now — "add a unit when it's ready" is exactly that), `source_key` idempotency, the validate/commit service, and the whole tenant/XP discipline.

**What changes:** the front door, and who decides which day a lesson lands on.

---

## Ground rules

- Same as always: house comment style, tenant-first repository rule, zero new backend dependencies, an Alembic migration for every schema change (head is now **`e5a2b8d17c40`**), `npm run test:e2e` green before done.
- **The teacher is a competent adult in a hurry, not a data-entry clerk.** Every screen in this phase is judged by how few actions a real Sunday-evening review takes.
- No `alert()` / `confirm()`. `ScheduleView.vue` uses three of them today; replace them as you touch that file.

---

## Item 1 — "Add a Unit": paste a list of titles

**The new front door, and the primary way curriculum enters the app from now on.**

One screen. Pick a program, name the unit, paste lesson titles one per line, choose a rhythm (item 2), press the button.

```
Program:  [ Beast Academy            v ]
Unit:     [ BA 2C — Measurement        ]   Status: ( ) Release now  (•) Add as planned
Rhythm:   [ Mon, Wed  v ]  (item 2)

Lessons — one per line:
┌──────────────────────────────────────┐
│ Ch 1: Measuring Length               │
│ Ch 1 Practice                        │
│ Ch 2: Weight & Volume                │
└──────────────────────────────────────┘

                              [ Add 3 lessons ]
```

**This is not a third ingest path.** It is a new *front end* over the Phase 2 service: the screen turns pasted lines into the same canonical rows `build_plan`/`commit_plan` already take, so there is one parser, one validator, one commit, one idempotency rule. Review §5.1's "one bulk path, one single-item path" still holds — the bulk path simply grew a door that does not involve a file.

**Defaults, so a bare title is enough:** `task_type: lesson`, `priority: standard`, `estimated_minutes: 30`, `xp_reward: 10`, `sequence_order` from line order. Every one of these is editable afterward on the unit's lesson list; none of them should block getting the unit in.

**Per-line overrides, optional and forgiving.** A trailing `[...]` on a line sets fields for that line — `Ch 1 Practice [practice, 20m, 15xp]` — parsed leniently and ignored (with a row-numbered warning, not an error) if it does not make sense. A teacher who never learns this syntax loses nothing.

**Fold the CSV screen into this one.** `/admin/import` becomes the same route with paste as the default and a small *"import a CSV file instead"* toggle revealing the Phase 2 screen. One nav item, called **Add Curriculum**. The CSV path stays because it is tested, it is the migration escape hatch, and it costs nothing sitting behind a link — but it stops being the thing the teacher meets first.

**Acceptance:** pasting 12 lines into an empty program creates 12 lessons in a new unit, all staged, in paste order; re-adding the same unit and lines reports them unchanged rather than duplicating (same `source_key` rule as Phase 2); a blank line is skipped, not an error.

---

## Item 2 — The unit's rhythm

**The teacher's answer to "space it out how I want," without 22 individual placements.**

A rhythm is a set of weekdays — `Mon,Wed` — chosen when the unit is added and changeable afterward. Applying a rhythm writes `day_of_week_hint` onto that unit's lessons in rotation, which is all the scheduler needs: `get_school_days` already searches forward for a hint match, so 22 lessons hinted Mon/Wed/Mon/Wed lay themselves across eleven weeks with no scheduler change at all. That mechanic is proven — it is what the corrected Tuttle CSV did.

**Where it lives.** Add `Unit.cadence` (`String(40)`, nullable) plus an Alembic migration off `e5a2b8d17c40`. Storing it — rather than only writing hints and forgetting — is what makes the rhythm visible in the unit panel and re-appliable when the teacher changes his mind. Lessons keep their per-lesson hint as the authoritative value; `cadence` is the recipe that generated them.

**Re-applying is explicit,** never automatic: a *"Re-space this unit"* button on the unit, which rewrites hints for that unit's **incomplete** lessons only. Completed work keeps its history, and pinned dates (`date_locked`) are skipped — a rhythm is a default, and a pin is a promise.

**Acceptance:** a unit added with `Mon,Wed` and 22 lessons produces alternating Mon/Wed hints; recalculating places them across eleven weeks rather than five; changing the rhythm to `Tue,Thu` and re-spacing moves the incomplete ones and leaves completed and pinned ones alone.

---

## Item 3 — The week planner

**The Sunday-evening screen. This is the centre of the phase**; items 1 and 2 feed it.

Replaces the read-only `WeeklyGrid.vue` (Mon–Thu, no interaction) and takes over `/admin/schedule`. Four capabilities, all requested:

**3a — The week at a glance.** Mon–Fri, every subject, each day showing its lesson count and total estimated minutes, with a visible marker when a day exceeds a comfortable load (reuse `daily_task_cap`, review §6.1). Next week is the default view — it is a *look ahead* — with arrows to move between weeks. Fix the timezone bug while you are here: `WeeklyGrid.vue` builds dates with `toISOString()`, which is exactly the UTC-shift trap `TaskForm.vue`'s `todayISO()` documents avoiding.

**3b — Move work between days.** Drag a card to another day, or a keyboard-reachable equivalent (a day picker on the card — drag alone is not an accessible control). **A moved lesson is pinned** (`date_locked = true`) automatically, because a hand-placed date the next sick day silently undoes is worse than no move at all. Show the pin on the card, and let it be removed to hand the lesson back to the scheduler.

**3c — Add or remove a day's work.** A `+` on any day opens the existing task form pre-dated to that day. On a card: *push to next week*, and *unassign* — which removes it from this student without deleting the lesson (review §9 item 15, B8). `POST /api/assignments` and a real unassign endpoint land here.

**3d — Flag what's behind.** A strip above the grid: what was scheduled before today and is not done, with three actions each — **catch up** (place it in the week ahead), **push** (let the scheduler re-flow it), **let it go** (unassign). This is the teacher's half of the day cap: the student's day gets a ceiling (`daily_task_cap`, oldest-first catch-up beyond it), and the backlog surfaces *here*, where an adult can decide about it, instead of silently stacking on a nine-year-old's morning.

**Acceptance:** the planner shows next week by default and flags an overloaded day; dragging a lesson to Friday pins it there and it survives adding a sick day; unassigning leaves the lesson and the unit intact; a student with more outstanding work than the cap sees the cap, and the teacher sees the overflow in the behind-strip.

---

## Order of work

```
1  ──► Add a Unit (paste)      — front end over the Phase 2 service; no schema change
2  ──► Unit.cadence + re-space — one small migration
3d ──► day cap + behind-strip  — the student-side protection, needed most
3a ──► week grid, read path
3b ──► move + pin
3c ──► add / push / unassign   — needs POST /api/assignments
```

Items 1 and 2 are shippable together and immediately useful — they are what unblocks loading Beast Academy the new way.

---

## Out of scope

- **Recurring routines** (the 14 definitions). Still real, still deferred — the weekly loop must feel right before another concept enters it. Next phase.
- Gamification of any kind. Parked at the owner's request.
- Any renaming of `courses`/`modules` API paths.
- Multi-student. The fan-out fix in item 3c helps, but full multi-student is not this phase.

---

## Known traps

1. **`toISOString()` for local dates** — the UTC-shift bug, live in `WeeklyGrid.vue:14`. Use the `todayISO()`/`isoDate()` pattern.
2. **A moved lesson that is not pinned goes back where it was** on the next sick day, holiday, or calendar deletion — `routers/schedule.py` fires a full-tenant recalculation on all three.
3. **Unassign is not delete.** `delete_task` removes the *lesson* and cascades (B8). Item 3c's unassign must remove the assignment only, and reverse that student's XP for it — through the ledger, never by deleting rows.
4. **Re-spacing must skip completed and pinned lessons**, or the first re-space quietly rewrites history and breaks a promise in the same click.
5. **Blank lines and stray whitespace** are the normal state of a pasted list. Strip and skip; never make a teacher hunt for an invisible character.
6. **`daily_task_cap` has no reader yet.** It is named in review §5.8 and was never wired up; item 3d is where it becomes real. Default 6.

---

## Done when

- [ ] A unit can be added by pasting titles, with a rhythm, in one screen and one click
- [ ] The CSV importer lives behind a link on that same screen, still working, still tested
- [ ] `Unit.cadence` persists the rhythm; re-spacing rewrites incomplete, unpinned hints only — with a test
- [ ] The week planner shows next week, flags overloaded days, and moves work between days with a pin — with a test that a moved lesson survives a sick day
- [ ] Work can be added, pushed, or unassigned from the planner; unassign leaves the lesson intact — with a test
- [ ] The student's day is capped, and the overflow is visible to the teacher in the behind-strip — with a test
- [ ] `npm run test:e2e` passes; `/health/ready` reports the new revision after deploy
- [ ] Beast Academy's next unit goes in through the new front door, by the teacher, without a spreadsheet
