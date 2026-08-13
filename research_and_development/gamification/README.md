# 🔬 Gamification — Research & Development Quarantine

**Status:** Decoupled from main app — awaiting future reintegration.  
**Quarantined:** 2026-08-12 (Pre-launch stability audit)

---

## What's Here

This directory contains all features related to the **XP Economy**, **Digital Pet (Sparky)**, and **Battle/Quest Arena** that have been safely extracted from the main application flow.

These features were removed to ensure **operational stability** for day-one homeschool launch. They can be reactivated once the core LMS loop is verified stable.

---

## Quarantined Files

| File | Original Location | Description |
|---|---|---|
| `pages/pet_arena.py` | `pages/student/pet_arena.py` | Sparky's Spore Evolution, Skill Tree, Trivia Battle, Dungeon, Side Quests |
| `pages/reward_store.py` | `pages/student/reward_store.py` | XP Economy store (pet-care tiers + real-world rewards) |
| `pages/store_manager.py` | `pages/admin/store_manager.py` | Admin inventory & reward claim management |
| `database_stubs.py` | `database.py` (extracted functions) | All gamification DB operations (pet XP, leveling, skill tree, side quests) |

---

## How to Reactivate

1. Move `pages/*.py` back to their original `pages/student/` or `pages/admin/` locations.
2. Merge `database_stubs.py` functions back into `database.py`.
3. Restore the pet mutation blocks in `complete_task()` and `complete_creator_project()`.
4. Re-add the page entries to `app.py` navigation.

---

## Notes

- The SQLite tables (`pet_status`, `pet_inventory`, `pet_unlocked_skills`, `pet_quests`, `side_quests`, `quest_completions`) are **still present in `flokus.db`** — no data was dropped.  
- The `rewards` and `purchases` tables remain **active** in the core app — real-world reward claiming still works through the Finances admin view.
- XP is still earned and tracked via the `tasks` and `creator_projects` tables — the economy math (`get_xp_balance()`) is unchanged.
