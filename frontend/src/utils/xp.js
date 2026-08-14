/**
 * Effective XP for a task, including the boss-fight multiplier.
 *
 * Must stay in step with `lesson_xp()` in backend/app/routers/tasks.py — that
 * is what the ledger actually awards. Kept in one place so the KPI row and the
 * task card can never disagree about what a boss fight is worth.
 */
export function taskXp(task) {
  return (task?.xp_reward || 0) * (task?.is_boss_fight ? 2 : 1)
}
