import streamlit as st
import database
from ui.auth import is_admin, render_login_sidebar



if not is_admin():
    render_login_sidebar()
    st.error("Access Denied. Administrator privileges required.")
    st.stop()

st.title("XP Store")

st.subheader("Store Inventory Management")

st.write("**Add a New Reward**")
with st.form("new_reward_form"):
    reward_name = st.text_input("Reward Name (e.g., '1 Hour Screen Time', '$5 Robux')")
    reward_cost = st.number_input("XP Cost", min_value=10, max_value=5000, value=100, step=10)
    reward_qty = st.number_input("Quantity in Stock", min_value=1, max_value=100, value=5, step=1)
    submitted_reward = st.form_submit_button("Add to Store")
    
    if submitted_reward and reward_name != "":
        database.add_reward(reward_name, reward_cost, reward_qty)
        st.success(f"Added {reward_name} to the store!")
        st.rerun()
        
st.divider()
st.write("**Current Store Items**")
rewards = database.get_rewards()
if len(rewards) == 0:
    st.info("No rewards in the store yet.")
else:
    for reward in rewards:
        reward_id, reward_name, reward_cost, reward_qty = reward
        
        col_rew1, col_rew2, col_rew3, col_rew4 = st.columns([0.4, 0.2, 0.2, 0.2])
        with col_rew1:
            st.markdown(f"🎁 **{reward_name}**")
        with col_rew2:
            edited_cost = st.number_input(
                "Cost", min_value=5, max_value=10000, value=int(reward_cost), step=5, 
                key=f"edit_cost_{reward_id}", label_visibility="collapsed"
            )
        with col_rew3:
            edited_qty = st.number_input(
                "Stock", min_value=0, max_value=500, value=int(reward_qty), step=1, 
                key=f"edit_qty_{reward_id}", label_visibility="collapsed"
            )
        with col_rew4:
            if edited_cost != reward_cost or edited_qty != reward_qty:
                if st.button("💾 Save", key=f"save_rew_{reward_id}"):
                    database.update_reward_details(reward_id, edited_cost, edited_qty)
                    st.rerun()
            else:
                if st.button("❌", key=f"del_reward_{reward_id}"):
                    database.delete_reward(reward_id)
                    st.rerun()
                
st.divider()
st.subheader("🎟️ Claimed & Pending Rewards Log")
st.caption("Approve and track Sonny's real-world reward claims.")

purchases_list = database.get_all_purchases()

if len(purchases_list) == 0:
    st.info("Sonny hasn't purchased any rewards yet.")
else:
    for p_id, r_name, cost, p_date, is_claimed in purchases_list:
        col_p1, col_p2, col_p3 = st.columns([0.5, 0.3, 0.2])
        with col_p1:
            status_emoji = "✅" if is_claimed == 1 else "⏳"
            st.markdown(f"{status_emoji} **{r_name}** — 💎 {cost} XP")
            st.caption(f"Purchased: {p_date}")
        with col_p2:
            if is_claimed == 1:
                st.markdown("<span style='color: #48bb78; font-weight: bold;'>Claimed</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #ed8936; font-weight: bold;'>Pending Claim</span>", unsafe_allow_html=True)
        with col_p3:
            if is_claimed == 0:
                if st.button("Mark Claimed", key=f"claim_btn_{p_id}", use_container_width=True):
                    database.mark_purchase_claimed(p_id)
                    st.success(f"Approved claim: {r_name}!")
                    st.rerun()
