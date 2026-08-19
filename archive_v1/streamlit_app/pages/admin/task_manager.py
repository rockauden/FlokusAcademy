"""
Task Manager -- the only place curriculum is added, scheduled or edited.

Three tabs, three jobs, no overlap:

    Import Curriculum   a whole program from a spreadsheet
    Quick Add           one lesson, right now
    Schedule            move, edit or delete what is already there

That replaces the previous three-way split, where the same job could be done
from a Quick Add form, from plus-buttons buried in each column of the weekly
grid, and from a "Master Curriculum Scheduler" that regenerated the entire year
from hardcoded Python tables. The last one is deleted: it rewrote 677
assignments on one click, and because the plan lived in curriculum_data.py
rather than a file, changing the curriculum meant editing source code. The year
it used to generate now lives in the database and exports to a spreadsheet, so
nothing was lost by removing it.
"""

import streamlit as st
from datetime import date, datetime, timedelta

import database
import config
import school_year
import curriculum_io

st.title("📝 Task Manager")
st.caption("Import a curriculum, add a one-off lesson, or adjust the schedule.")

tab_import, tab_quick, tab_schedule = st.tabs([
    "📥 Import Curriculum",
    "⚡ Quick Add Lesson",
    "🗓️ Schedule",
])

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri"]


# ==========================================================================
# TAB 1 -- IMPORT CURRICULUM
# ==========================================================================
with tab_import:
    st.subheader("📥 Import a curriculum")

    year = school_year.summary()
    st.caption(
        f"School year **{year['start']:%b %d, %Y} – {year['end']:%b %d, %Y}** · "
        f"{year['weeks']} weeks · {year['school_days']} school days · "
        f"{year['days_off']} days off. Imports schedule around the days off "
        f"automatically — nothing can land on a break."
    )

    with st.expander("What the file needs to look like", expanded=False):
        st.markdown(
            "One **sheet per program**, one **row per lesson**, in teaching "
            "order. Only `program` and `title` are required; everything else "
            "has a sensible default.\n\n"
            "**There is no date column, on purpose.** The file says *what* to "
            "teach and in what order. You say *when* — a start date and which "
            "weekdays the program runs — and Flokus schedules it against the "
            "school calendar. That way the file and the calendar can never "
            "disagree.\n\n"
            "**Weekly habits go on a `Routines` sheet**, listed once with a "
            "`day_of_week`, not repeated 36 times. Chess on Wednesdays is one "
            "row.\n\n"
            "**Re-importing is safe.** Fix a typo in Excel, load the same file "
            "again, and matching rows update instead of duplicating. Work "
            "Sonny has already completed is never touched."
        )
        st.code("program | unit | title | task_type | xp_reward | medium | resource_url",
                language="text")

    st.markdown("##### 1. Upload")
    upload = st.file_uploader("Curriculum spreadsheet (.xlsx or .csv)",
                              type=["xlsx", "xlsm", "csv"], key="curric_upload")

    if upload is not None:
        raw = upload.getvalue()
        lessons, routines, notes = curriculum_io.read_rows(upload.name, raw)
        lessons, routines, errors, warnings = curriculum_io.validate(lessons, routines)

        for n in notes:
            st.info(n)

        if errors:
            st.error(f"**{len(errors)} problem(s) found — nothing was imported.** "
                     "Fix these and upload again.")
            # Row-numbered so the message points at a real place in the file.
            for e in errors[:40]:
                st.markdown(f"- {e}")
            if len(errors) > 40:
                st.caption(f"…and {len(errors) - 40} more.")
        else:
            if warnings:
                with st.expander(f"⚠️ {len(warnings)} warning(s) — import can still proceed"):
                    for w in warnings:
                        st.markdown(f"- {w}")

            by_program = {}
            for r in lessons:
                by_program.setdefault(r.get("program", "?"), []).append(r)
            routine_programs = sorted({r.get("program", "?") for r in routines})

            st.success(
                f"✅ Read **{len(lessons)} lessons** across "
                f"{len(by_program)} program(s)"
                + (f" and **{len(routines)} routine definition(s)**." if routines else ".")
            )

            st.markdown("##### 2. Choose what to import")
            choices = sorted(by_program) + (["Routines only"] if routines else [])
            if not choices:
                st.warning("Nothing importable in this file.")
                st.stop()

            picked = st.selectbox(
                "Program", choices,
                help="One program at a time — each has its own weekly rhythm."
            )

            if picked == "Routines only":
                picked_lessons, picked_routines = [], routines
            else:
                picked_lessons = by_program[picked]
                picked_routines = [r for r in routines if r.get("program") == picked]

            col_a, col_b = st.columns([0.55, 0.45])
            with col_a:
                days = st.multiselect(
                    "Which days does this program run?",
                    DAY_ORDER, default=["Mon", "Tue", "Wed", "Thu"],
                    help="Mon–Thu carry new material. Friday is review and "
                         "catch-up — putting new curriculum there is usually a "
                         "mistake."
                )
            with col_b:
                # Until Sonny has actually completed something, the sensible
                # default is the first day of the year, not today -- otherwise
                # a full-year import on day two reports that one lesson won't
                # fit, which is technically true and completely unhelpful.
                any_done = any(done for _, _, done, _, _
                               in database.count_tasks_by_category())
                start = st.date_input(
                    "Start on",
                    value=max(date.today(), year["start"]) if any_done
                    else year["start"],
                    min_value=year["start"], max_value=year["end"]
                )

            if "Fri" in days:
                st.warning("Friday is the review and catch-up day. New "
                           "curriculum there will push against the light-Friday "
                           "design.")

            replace = st.checkbox(
                f"Replace this program's existing unfinished assignments from "
                f"{start:%b %d} onward",
                value=True,
                help="Leave on when re-loading a corrected plan. Turn off to "
                     "add alongside what is already scheduled. Completed work "
                     "is never removed either way."
            )

            weekday_nums = [school_year.WEEKDAY_NAMES[d] for d in days]
            if not weekday_nums:
                st.warning("Pick at least one day.")
            else:
                pv = curriculum_io.preview(picked_lessons, picked_routines,
                                           weekday_nums, start,
                                           replace_program=replace)

                st.markdown("##### 3. Preview")
                if pv["short_by"]:
                    st.error(
                        f"**{pv['short_by']} lessons won't fit.** There are only "
                        f"{pv['lesson_slots']} school days on "
                        f"{', '.join(days)} between {start:%b %d} and the end of "
                        f"the year, but this program has {pv['lesson_count']} "
                        f"lessons. Start earlier or add a weekday."
                    )
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Lessons", pv["lesson_count"])
                    m2.metric("First", f"{pv['lesson_first']:%b %d}" if pv["lesson_first"] else "—")
                    m3.metric("Last", f"{pv['lesson_last']:%b %d, %Y}" if pv["lesson_last"] else "—")

                    if pv["routines"]:
                        st.caption("Routines: " + " · ".join(
                            f"{t} ×{n}" for t, n in pv["routines"].items()))

                    # The quiet failure: the import is valid, fits the
                    # calendar, and simply makes Sonny's days too long. Usually
                    # it means the weekdays picked aren't the ones this program
                    # actually runs on.
                    if pv["over_cap_days"]:
                        st.warning(
                            f"⚠️ **{pv['over_cap_days']} day(s) would go over "
                            f"{school_year.MAX_TASKS_PER_DAY} assignments** "
                            f"(busiest: {pv['busiest']}), starting "
                            f"{pv['over_cap_first']:%b %d, %Y}. That usually "
                            f"means these aren't the days this program runs on "
                            f"— try fewer weekdays."
                        )
                    else:
                        st.caption(f"✅ Busiest day after this import: "
                                   f"{pv['busiest']} assignments.")

                    st.dataframe(
                        [{"#": i + 1, "Title": r["title"],
                          "Type": r.get("task_type", "") or "lesson",
                          "XP": r.get("xp_reward", "") or 10,
                          "Medium": (r.get("medium") or "offline").title()}
                         for i, r in enumerate(picked_lessons[:200])],
                        use_container_width=True, hide_index=True, height=260
                    )
                    if len(picked_lessons) > 200:
                        st.caption(f"Showing the first 200 of {len(picked_lessons)}.")

                    st.markdown("##### 4. Commit")
                    if st.button("📥 Import into the schedule",
                                 type="primary", use_container_width=True):
                        try:
                            res = curriculum_io.commit(
                                picked_lessons, picked_routines,
                                weekday_nums, start, replace_program=replace)
                        except Exception as exc:
                            st.error(f"Nothing was imported. {exc}")
                        else:
                            st.success(
                                f"🎉 Imported **{res['inserted']} new** and "
                                f"updated **{res['updated']}** assignment(s)"
                                + (f", clearing {res['removed']} superseded."
                                   if res["removed"] else ".")
                                + (f"  Scheduled {res['first']:%b %d, %Y} → "
                                   f"{res['last']:%b %d, %Y}." if res["first"] else "")
                            )
                            # Never let a cap thin the plan silently -- a
                            # schedule that quietly dropped work would read as
                            # "imported everything" when it didn't.
                            if res.get("skipped_full"):
                                st.info(
                                    f"ℹ️ {res['skipped_full']} routine "
                                    f"session(s) were left off days that were "
                                    f"already at {school_year.MAX_TASKS_PER_DAY} "
                                    f"assignments — build days and book "
                                    f"parties, mostly. Lessons are never "
                                    f"skipped this way."
                                )
                            st.rerun()

    st.divider()
    st.markdown("##### Export the current plan")
    st.caption("Writes every scheduled assignment back out in this same "
               "format — edit it in Excel and re-import, or hand it to V2.")
    if st.button("📤 Export to spreadsheet", use_container_width=True):
        out = curriculum_io.export_workbook("Flokus_Curriculum_2026-27_EXPORT.xlsx")
        st.success(f"Exported {out['rows']} assignments "
                   f"({out['lessons']} lessons + {out['routines']} routines) "
                   f"to `{out['path']}`")
        with open(out["path"], "rb") as fh:
            st.download_button("⬇️ Download the workbook", fh.read(),
                               file_name="Flokus_Curriculum_2026-27.xlsx",
                               mime="application/vnd.openxmlformats-officedocument."
                                    "spreadsheetml.sheet",
                               use_container_width=True)

    st.divider()
    st.markdown("##### What's loaded right now")
    for cat, n, done, first, last in database.count_tasks_by_category():
        emoji = config.SUBJECT_EMOJIS.get(cat, "📋")
        st.markdown(f"{emoji} **{cat}** — {n} assignments "
                    f"({done or 0} completed) · {first} → {last}")


# ==========================================================================
# TAB 2 -- QUICK ADD
# ==========================================================================
with tab_quick:
    st.subheader("⚡ Add a single lesson")
    st.write("For a one-off: a make-up assignment, a field trip, something "
             "Sonny asked for. Whole programs go through the importer.")

    with st.form("quick_task_form", clear_on_submit=True):
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            q_title = st.text_input(
                "Lesson description*",
                placeholder="e.g. Chapter 2, pages 15–20")
        with col2:
            q_cat = st.selectbox("Subject*", list(config.SUBJECT_EMOJIS.keys()))

        col3, col4, col5, col6 = st.columns([0.3, 0.24, 0.26, 0.2])
        with col3:
            q_date = st.date_input("Scheduled date", value=date.today())
        with col4:
            q_medium = st.selectbox("Medium*", ["Offline", "Online"],
                                    help="Offline (books, kits, paper) vs "
                                         "online (apps, screen)")
        with col5:
            q_url = st.text_input("Link (optional)",
                                  placeholder="https://youtube.com/…")
        with col6:
            q_xp = st.number_input("XP", min_value=5, max_value=500,
                                   value=10, step=5)

        if st.form_submit_button("🚀 Add to the schedule",
                                 use_container_width=True):
            if not q_title.strip():
                st.error("⚠️ The lesson needs a description.")
            else:
                # A day off is not an error -- a make-up session over spring
                # break is a legitimate thing to schedule. But it should be a
                # decision, not a surprise, so say so and let it through.
                reason = school_year.day_off_reason(q_date)
                database.add_task_to_db(
                    q_title.strip(), q_cat, q_url.strip() if q_url else "",
                    q_xp, q_date, 0, q_medium)
                msg = (f"🎉 Added **{q_title}** for {q_cat} on "
                       f"{q_date:%A, %b %d}.")
                if reason:
                    st.warning(f"{msg}  Heads up — that day is **{reason}**.")
                else:
                    st.success(msg)
                st.rerun()


# ==========================================================================
# TAB 3 -- SCHEDULE
# ==========================================================================
with tab_schedule:
    st.subheader("🗓️ Weekly schedule")
    st.write("Edit, move or delete anything already scheduled.")

    col_sel, col_nav = st.columns([0.45, 0.55])
    with col_sel:
        picked_day = st.date_input(
            "Week of", value=date.today() - timedelta(days=date.today().weekday()))
    monday = picked_day - timedelta(days=picked_day.weekday())

    week_days = [monday + timedelta(days=i) for i in range(5)]
    week_rows = {d: database.get_tasks_on_date(d) for d in week_days}
    total = sum(len(v) for v in week_rows.values())

    with col_nav:
        st.caption(f"Week of **{monday:%B %d, %Y}** · {total} assignments")

    # Screen-time balance, which is the reason the medium column exists.
    online = sum(1 for rows in week_rows.values() for r in rows if r[5] == "Online")
    if total:
        offline_pct = int(((total - online) / total) * 100)
        st.progress(offline_pct / 100.0,
                    text=f"{offline_pct}% offline books & kits · "
                         f"{100 - offline_pct}% online apps")
        if offline_pct < 40:
            st.warning("Over 60% of this week is screen-based. Consider "
                       "shifting a touchpoint offline.")

    st.divider()

    cols = st.columns(5)
    for i, day in enumerate(week_days):
        with cols[i]:
            off = school_year.day_off_reason(day)
            label = f"**{day:%A}**  \n*{day:%b %d}*"
            if day == date.today():
                st.markdown(f"📌 {label}")
            else:
                st.markdown(label)
            if day.weekday() == school_year.REVIEW_DAY:
                st.caption("Review & catch-up")
            st.divider()

            if off:
                st.info(f"🌴 {off}")
                continue

            rows = week_rows[day]
            if not rows:
                st.caption("Nothing scheduled.")

            for t_id, t_title, t_cat, t_url, t_xp, t_med, t_done, t_date in rows:
                emoji = config.SUBJECT_EMOJIS.get(t_cat, "📋")
                if t_done:
                    st.markdown(f"✅ ~~{emoji} {t_title}~~")
                    continue

                with st.container(border=True):
                    st.markdown(f"**{emoji} {t_title}**")
                    st.caption(f"{t_cat} · {'💻' if t_med == 'Online' else '📖'} "
                               f"{t_med} · 💎 {t_xp} XP")

                    # Widget keys carry the task id AND the column date. The id
                    # alone used to be enough only by luck: the grid read from
                    # get_pending_tasks(), which sweeps overdue work into
                    # today's column, so an assignment running late rendered in
                    # both its own column and today's -- and Streamlit raised
                    # StreamlitDuplicateElementKey right in the teacher's face.
                    # The grid now queries an exact date, and the keys are
                    # namespaced so a future change cannot reintroduce it.
                    k = f"{t_id}_{day.isoformat()}"
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.popover("✏️", use_container_width=True):
                            e_title = st.text_input("Title", value=t_title,
                                                    key=f"g_title_{k}")
                            cats = list(config.SUBJECT_EMOJIS.keys())
                            e_cat = st.selectbox(
                                "Subject", cats,
                                index=cats.index(t_cat) if t_cat in cats else 0,
                                key=f"g_cat_{k}")
                            e_med = st.selectbox(
                                "Medium", ["Offline", "Online"],
                                index=0 if t_med != "Online" else 1,
                                key=f"g_med_{k}")
                            e_xp = st.number_input(
                                "XP", min_value=5, max_value=500,
                                value=int(t_xp), step=5, key=f"g_xp_{k}")
                            e_date = st.date_input("Move to", value=day,
                                                   key=f"g_date_{k}")
                            if st.button("Save", key=f"g_save_{k}"):
                                if not e_title.strip():
                                    st.error("Title cannot be empty.")
                                else:
                                    database.update_task_details(
                                        t_id, e_title.strip(), e_cat, t_url or "",
                                        e_xp, e_date, 0, e_med)
                                    st.rerun()
                    with c2:
                        with st.popover("🗑️", use_container_width=True):
                            st.write("Delete this assignment?")
                            if st.button("Confirm", key=f"g_del_{k}"):
                                database.delete_task(t_id)
                                st.rerun()
