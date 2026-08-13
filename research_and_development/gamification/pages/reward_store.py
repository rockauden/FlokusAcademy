import streamlit as st
import database

# Ensure DB initialized & recalibrated
database.init_db()

st.title("🛍️ Flokus Academy Reward Store & XP Economy")
st.caption("Spend your earned XP Bank on digital pet care, extra screen time, cash allowances, and video games!")

# Fetch balances
bank_balance = database.get_xp_balance()
pet = database.get_pet_status()
pet_level = pet[2] if pet else 1
spore_stage = pet[10] if pet else "Spore"
sp_points = database.get_pet_skill_points()

# --- ECONOMY TRANSPARENCY HERO ---
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1:
    st.metric("🏦 Spendable XP Bank", f"💎 {bank_balance} XP", help="Earned from daily lessons, boss fights, trivia & quests.")
with col_h2:
    st.metric("🐾 Sparky's Evolutionary Level", f"Lvl {pet_level} ({spore_stage})", help="Leveled up by completing daily schoolwork.")
with col_h3:
    st.metric("⭐ Skill Points Available", f"{sp_points} SP", help="Earned on level ups & side quests. Spend in Constellation Skill Web.")

with st.expander("ℹ️ How the Flokus Economy Works (Earnings & Effort Guide)", expanded=False):
    st.markdown(
        """
        - 📋 **Daily Core Lesson**: **+15 XP** (+1 Stat boost to Sparky)
        - 👑 **Daily Boss Fight**: **+30 XP** (Double XP Challenge!)
        - ⚔️ **Trivia Guardian Victory**: **+25 XP** + **+1 Skill Point**
        - 📜 **Side Quest Completion**: **+30 XP** + **+1 to +2 Skill Points**
        - 🛠️ **Creator Project Milestone**: **+50 to +100 XP**
        - 🌟 **Weekly Completion Bonus**: **+100 XP** Streak Bonus!
        """
    )

st.divider()

# Fetch all rewards
rewards = database.get_rewards()

if len(rewards) == 0:
    st.info("The store is currently empty. Dad needs to stock the shelves!")
else:
    # Categorize rewards into 4 tiers
    tier_pet = [r for r in rewards if any(k in r[1].lower() for k in ["protein", "chip", "ink", "soda", "treat", "matrix", "pet"])]
    tier_privileges = [r for r in rewards if any(k in r[1].lower() for k in ["gaming", "youtube", "screen", "time"])]
    tier_currencies = [r for r in rewards if any(k in r[1].lower() for k in ["cash", "allowance", "minecoins", "shiny rocks", "robux"])]
    tier_major = [r for r in rewards if any(k in r[1].lower() for k in ["day off", "new game", "game (up to"])]
    
    # Catch any uncategorized items into major or pet tier
    all_categorized = set(r[0] for r in (tier_pet + tier_privileges + tier_currencies + tier_major))
    uncategorized = [r for r in rewards if r[0] not in all_categorized]
    tier_major.extend(uncategorized)
    
    # --- 4 STORE TABS ---
    tab_p, tab_screen, tab_cash, tab_maj = st.tabs([
        "🎒 Pet Care (5 - 25 XP)",
        "🎮 Screen Time & Perks (50 - 100 XP)",
        "💵 Cash & Game Currencies (250 - 300 XP)",
        "🏆 Major Rewards (750 - 1000 XP)"
    ])
    
    def render_reward_cards(item_list):
        if not item_list:
            st.caption("No items in this tier currently.")
            return
            
        cols = st.columns(3)
        for idx, reward in enumerate(item_list):
            reward_id, reward_name, reward_cost, reward_qty = reward
            
            pct_saved = min(bank_balance / reward_cost, 1.0) if reward_cost > 0 else 1.0
            can_afford = (bank_balance >= reward_cost and reward_qty > 0)
            
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"#### {reward_name}")
                    st.markdown(f"**Cost:** 💎 `{reward_cost} XP`")
                    
                    if reward_qty > 0:
                        st.caption(f"🟢 In Stock: {reward_qty} available")
                    else:
                        st.caption("🔴 OUT OF STOCK")
                        
                    # Savings progress bar for rewards costing >= 50 XP
                    if reward_cost >= 50:
                        if can_afford:
                            st.progress(1.0, text="✨ 100% Saved - Ready to Redeem!")
                        else:
                            st.progress(pct_saved, text=f"Savings: {bank_balance} / {reward_cost} XP ({int(pct_saved * 100)}%)")
                            
                    st.write("")
                    
                    if reward_qty <= 0:
                        st.button("Out of Stock", key=f"btn_out_{reward_id}", disabled=True, use_container_width=True)
                    elif can_afford:
                        with st.popover("🛍️ Redeem Reward", use_container_width=True):
                            st.write(f"Spend 💎 `{reward_cost} XP` on **{reward_name}**?")
                            if st.button("Confirm Purchase", key=f"confirm_buy_{reward_id}", use_container_width=True):
                                database.buy_reward(reward_id, reward_name, reward_cost)
                                st.balloons()
                                st.success(f"🎉 Successfully bought {reward_name}!")
                                st.rerun()
                    else:
                        needed = reward_cost - bank_balance
                        st.button(f"Need {needed} XP More", key=f"btn_need_{reward_id}", disabled=True, use_container_width=True)

    with tab_p:
        st.subheader("🎒 Digital Pet Care & Energy Items")
        st.write("Keep Sparky energized, restore stamina, and unlock rare chameleon effects for low XP costs!")
        render_reward_cards(tier_pet)

    with tab_screen:
        st.subheader("🎮 Screen Time & Privileges")
        st.write("Earn extra YouTube & video gaming time by completing your daily schoolwork!")
        render_reward_cards(tier_privileges)

    with tab_cash:
        st.subheader("💵 Cash Allowance & In-Game Currencies")
        st.write("Convert your hard-earned study XP into real cash allowance or Minecraft & Gorilla Tag currencies!")
        render_reward_cards(tier_currencies)

    with tab_maj:
        st.subheader("🏆 Major Rewards & Milestone Achievements")
        st.write("Save up your XP over weeks of consistent effort to earn mental health days off or brand-new video games!")
        render_reward_cards(tier_major)
