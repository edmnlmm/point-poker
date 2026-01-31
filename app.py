import streamlit as st
import pandas as pd
import os
import json
import time

# --- CONFIGURATION & SECURITY ---
DB_FILE = "poker_data.json"

try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
except Exception:
    ADMIN_PASSWORD = "GRCCRISPYCRITTERS" # Default

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"votes": {}, "revealed": False}
    return {"votes": {}, "revealed": False}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- APP CONFIG ---
st.set_page_config(page_title="Agile Cards", page_icon="🃏", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    div.stButton > button {
        height: 100px; width: 70px; border-radius: 12px;
        border: 2px solid #4CAF50; background-color: white;
        color: #4CAF50; font-size: 24px; font-weight: bold;
        transition: all 0.2s; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background-color: #4CAF50; color: white; transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)

data = load_data()
is_admin_route = st.query_params.get("role") == "admin"
authenticated = False

# --- SIDEBAR ---
st.sidebar.title("🃏 Poker Lounge")
user_name = st.sidebar.text_input("Your Name", placeholder="Enter name...")

if is_admin_route:
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        authenticated = True

# --- MAIN UI ---
st.title("Pointing Poker")

if not user_name:
    st.info("👈 Please enter your name in the sidebar to enter.")
    st.stop()

if authenticated:
    st.subheader("Admin Dashboard")
    c1, c2 = st.columns(2)
    if c1.button("🔓 Reveal Scores", use_container_width=True):
        data["revealed"] = True
        save_data(data)
    if c2.button("🔄 Reset Table", use_container_width=True):
        save_data({"votes": {}, "revealed": False})
        st.rerun()
    st.divider()

# --- VOTING ---
st.write(f"### Vote, {user_name}:")
cards = ["1", "2", "3", "5", "8", "13", "21", "☕"]
cols = st.columns(len(cards))
for i, card in enumerate(cards):
    if cols[i].button(card):
        data["votes"][user_name] = card
        save_data(data)
        st.toast(f"Voted {card}")

# --- RESULTS ---
st.divider()
if data["revealed"]:
    st.subheader("Results Distribution")
    if data["votes"]:
        # Prepare Data
        df = pd.DataFrame(list(data["votes"].items()), columns=["User", "Estimate"])
        
        # 1. Grouping for Table
        summary = df.groupby("Estimate").agg(
            Count=("User", "count"),
            Voters=("User", lambda x: ", ".join(x))
        ).reset_index()
        
        # Sort logic
        summary['sort_val'] = pd.to_numeric(summary['Estimate'], errors='coerce').fillna(999)
        summary = summary.sort_values('sort_val').drop(columns=['sort_val'])
        
        # 2. Visualization (Bar Chart)
        # Create a chart-friendly dataframe
        chart_data = summary.set_index("Estimate")[["Count"]]
        st.bar_chart(chart_data, color="#4CAF50")

        # 3. Detailed Table
        st.table(summary)
        
        # 4. Live Average
        nums = [int(v) for v in data["votes"].values() if v.isdigit()]
        if nums:
            st.metric("Current Average", f"{sum(nums)/len(nums):.1f}")
    else:
        st.write("No votes cast.")
else:
    st.subheader("The Table")
    if data["votes"]:
        voter_cols = st.columns(4)
        for idx, player in enumerate(data["votes"].keys()):
            with voter_cols[idx % 4]:
                st.success(f"✅ {player}")
    else:
        st.write("Waiting for votes...")

# --- SYNC ---
time.sleep(2)
st.rerun()