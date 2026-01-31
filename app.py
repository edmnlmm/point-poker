import streamlit as st
import pandas as pd
import os
import json
import hashlib

# --- CONFIGURATION ---
DB_FILE = "poker_data.json"

try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
except Exception:
    ADMIN_PASSWORD = "GRCCRISPYCRITTERS"

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

# Helper to check if data has changed to avoid unnecessary re-renders
def get_data_hash():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    return ""

# --- APP CONFIG ---
st.set_page_config(page_title="Agile Cards", page_icon="🃏", layout="centered")

# --- FIXED CUSTOM CSS ---
st.markdown("""
<style>
    /* target only the card buttons using their key-prefix */
    div[data-testid="stHorizontalBlock"] button {
        height: 100px; 
        width: 75px; 
        border-radius: 12px;
        border: 2px solid #4CAF50; 
        background-color: white;
        color: #4CAF50; 
        font-size: 24px; 
        font-weight: bold;
        transition: all 0.2s; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    /* Ensure admin buttons look normal and fit their text */
    div[data-testid="stVerticalBlock"] div[data-testid="stColumn"] button {
        width: 100% !important;
        height: auto !important;
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# State management for "smart refresh"
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_data_hash()

data = load_data()
is_admin_route = st.query_params.get("role") == "admin"
authenticated = False

# --- SIDEBAR ---
st.sidebar.title("🃏 Poker Lounge")
user_name = st.sidebar.text_input("Your Name", placeholder="Enter name...")

# Add a manual refresh button for users to pull latest data without a loop
if st.sidebar.button("🔄 Sync Table"):
    st.rerun()

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
    # Admin buttons now have automatic width to fit text
    if c1.button("🔓 Reveal Scores"):
        data["revealed"] = True
        save_data(data)
        st.rerun()
    if c2.button("🔄 Reset Table"):
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
        # When a user votes, we force a rerun to update their view
        st.rerun()

# --- RESULTS ---
st.divider()
if data["revealed"]:
    st.subheader("Results Distribution")
    if data["votes"]:
        df = pd.DataFrame(list(data["votes"].items()), columns=["User", "Estimate"])
        summary = df.groupby("Estimate").agg(
            Count=("User", "count"),
            Voters=("User", lambda x: ", ".join(x))
        ).reset_index()
        
        summary['sort_val'] = pd.to_numeric(summary['Estimate'], errors='coerce').fillna(999)
        summary = summary.sort_values('sort_val').drop(columns=['sort_val'])
        
        st.bar_chart(summary.set_index("Estimate")[["Count"]], color="#4CAF50")
        st.table(summary)
        
        nums = [int(v) for v in data["votes"].values() if v.isdigit()]
        if nums:
            st.metric("Average Score", f"{sum(nums)/len(nums):.1f}")
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

# --- SMART REFRESH CHECK ---
# Check if the file on disk has changed since we last loaded it
current_hash = get_data_hash()
if current_hash != st.session_state.last_hash:
    st.session_state.last_hash = current_hash
    st.rerun()