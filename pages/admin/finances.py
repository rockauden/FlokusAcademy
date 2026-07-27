import streamlit as st
import pandas as pd
import database
from ui.auth import is_admin, render_login_sidebar



if not is_admin():
    render_login_sidebar()
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

st.title("UFA Finances")

expenses = database.get_all_expenses()
df_expenses_export = pd.DataFrame(expenses, columns=["ID", "Item Name", "Cost", "Category", "Status"])
if not df_expenses_export.empty:
    df_expenses_export = df_expenses_export.drop(columns=["ID"])

col_title, col_export = st.columns([0.7, 0.3])
with col_title:
    st.subheader("Utah Fits All (UFA) Budget Tracker")
with col_export:
    if not df_expenses_export.empty:
        csv_data = df_expenses_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Expenses to CSV",
            data=csv_data,
            file_name="Flokus_UFA_Expenses.csv",
            mime="text/csv",
            key="export_expenses_csv",
            use_container_width=True
        )
        
total_budget = 4000.00
total_spent = sum([expense[2] for expense in expenses if expense[4] != "Out of Pocket (Not UFA)"])
remaining_budget = total_budget - total_spent

col1, col2, col3 = st.columns(3)
col1.metric("Total UFA Grant", f"${total_budget:,.2f}")
col2.metric("Total Spent", f"${total_spent:,.2f}")
col3.metric("Remaining Funds", f"${remaining_budget:,.2f}")

# --- NEW: Budget Alerts ---
if remaining_budget < 600.00:
    st.error(f"⚠️ **Low Funds Warning!** Remaining UFA budget is ${remaining_budget:,.2f} (under 15%). Plan purchases carefully!")
elif remaining_budget < 1200.00:
    st.warning(f"⚠️ **Budget Alert:** Remaining UFA budget is ${remaining_budget:,.2f} (under 30%).")
# --- END NEW ---

st.sidebar.markdown("---")

st.write("**UFA Pipeline Allocation Radar**")
status_map = database.get_expense_totals_by_status()
pending_odyssey = status_map.get("Pending Odyssey Approval", 0.0)
direct_paid = status_map.get("Approved & Direct Paid", 0.0)
reimbursed = status_map.get("Reimbursed", 0.0)
out_of_pocket = status_map.get("Out of Pocket (Not UFA)", 0.0)

radar_col1, radar_col2, radar_col3, radar_col4 = st.columns(4)
radar_col1.metric("⏳ Pending Odyssey", f"${pending_odyssey:,.2f}")
radar_col2.metric("🟢 Direct Paid", f"${direct_paid:,.2f}")
radar_col3.metric("💰 Reimbursed", f"${reimbursed:,.2f}")
radar_col4.metric("🛑 Out of Pocket", f"${out_of_pocket:,.2f}")
st.divider()

# --- NEW: Financial Charts Section ---
if not df_expenses_export.empty:
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### 📊 UFA Budget Spent by Category")
        df_cat_totals = df_expenses_export[df_expenses_export["Status"] != "Out of Pocket (Not UFA)"].groupby("Category")["Cost"].sum().reset_index()
        if not df_cat_totals.empty:
            df_cat_totals = df_cat_totals.set_index("Category")
            st.bar_chart(df_cat_totals)
        else:
            st.info("No UFA expenses logged yet.")
    with chart_col2:
        st.markdown("#### ⏳ Spent by Status Pipeline")
        df_status_totals = df_expenses_export.groupby("Status")["Cost"].sum().reset_index()
        if not df_status_totals.empty:
            df_status_totals = df_status_totals.set_index("Status")
            st.bar_chart(df_status_totals)
        else:
            st.info("No expenses logged yet.")
    st.divider()
# --- END NEW ---

st.write("**Log a New Purchase**")
with st.form("expense_form"):
    item_name = st.text_input("Item/Service Name")
    cost = st.number_input("Cost ($)", min_value=0.00, format="%.2f")
    category = st.selectbox("Category", [
        "Curriculum & Workbooks", "Technology/Hardware", 
        "Extracurricular/Classes", "Supplies & Materials"
    ])
    status = st.selectbox("Status", [
        "Pending Odyssey Approval", "Approved & Direct Paid", 
        "Reimbursed", "Out of Pocket (Not UFA)"
    ])
    submit_expense = st.form_submit_button("Log Expense")
    if submit_expense:
        if item_name.strip() == "":
            st.error("⚠️ Item/Service Name cannot be empty!")
        else:
            database.add_expense(item_name.strip(), cost, category, status)
            st.success("Expense logged successfully!")
            st.rerun()

st.write("**Expense History**")
if len(expenses) == 0:
    st.info("No expenses logged yet.")
else:
    for exp in expenses:
        col_exp1, col_exp2, col_exp3 = st.columns([0.5, 0.3, 0.2])
        with col_exp1:
            st.markdown(f"📦 **{exp[1]}** | ${exp[2]:.2f}\n\n*Category: {exp[3]}*")
        with col_exp2:
            status_options = [
                "Pending Odyssey Approval", "Approved & Direct Paid", 
                "Reimbursed", "Out of Pocket (Not UFA)"
            ]
            
            try:
                current_status_idx = status_options.index(exp[4])
            except ValueError:
                current_status_idx = 0
                
            chosen_status = st.selectbox(
                f"Status Dropdown {exp[0]}",
                options=status_options,
                index=current_status_idx,
                key=f"update_status_select_{exp[0]}",
                label_visibility="collapsed"
            )
            
            if chosen_status != exp[4]:
                database.update_expense_status(exp[0], chosen_status)
                st.rerun()
        with col_exp3:
            col_edit, col_del = st.columns(2)
            with col_edit:
                with st.popover("✏️"):
                    edit_exp_name = st.text_input("Item Name", value=exp[1], key=f"edit_exp_name_{exp[0]}")
                    edit_exp_cost = st.number_input("Cost ($)", min_value=0.00, value=float(exp[2]), format="%.2f", key=f"edit_exp_cost_{exp[0]}")
                    edit_exp_cat = st.selectbox(
                        "Category",
                        options=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"],
                        index=["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"].index(exp[3]) if exp[3] in ["Curriculum & Workbooks", "Technology/Hardware", "Extracurricular/Classes", "Supplies & Materials"] else 0,
                        key=f"edit_exp_cat_{exp[0]}"
                    )
                    edit_exp_status = st.selectbox(
                        "Status",
                        options=status_options,
                        index=current_status_idx,
                        key=f"edit_exp_status_{exp[0]}"
                    )
                    if st.button("Save", key=f"save_exp_{exp[0]}"):
                        if edit_exp_name.strip() == "":
                            st.error("Name cannot be empty!")
                        else:
                            database.update_expense_details(exp[0], edit_exp_name.strip(), edit_exp_cost, edit_exp_cat, edit_exp_status)
                            st.success("Expense updated!")
                            st.rerun()
            with col_del:
                with st.popover("❌"):
                    st.write("Delete this expense?")
                    if st.button("Confirm", key=f"del_exp_confirm_{exp[0]}"):
                        database.delete_expense(exp[0])
                        st.rerun()
