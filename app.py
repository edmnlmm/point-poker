import streamlit as st
import pandas as pd
import os
import json
import time

# --- CONFIGURATION & SECURITY ---
DB_FILE = "poker_data.json"

# Safe way to get secrets without crashing locally or in deployment
try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
except Exception:
    ADMIN_PASSWORD = "admin123" # Local fallback/default

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

# --- CUSTOM CSS FOR CARDS ---
# Corrected the keyword to unsafe_allow_html
st.markdown("""
<style>
    /* Style the buttons to look like poker cards */
    div.stButton > button {
        height: 120px;
        width: 80px;
        border-radius: 12px;
        border: 2px solid #4CAF50;
        background-color: white;
        color: #4CAF50;
        font-size: 28px;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div.stButton > button:hover {
        background-color: #4CAF50;
        color: white;
        transform: translateY(-8px);
        box-shadow: 3px 10px 15px rgba(0,0,0,0.2);
    }
    div.stButton > button:active {
        transform: translateY(0);
    }
    /* Style for the average metric */
    [data-testid="stMetricValue"] {
        font-size: 40px;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION LOGIC ---
data = load_data()
query_params = st.query_params
is_admin_route = query_params.get("role") == "admin"
authenticated = False

# --- SIDEBAR ---
st.sidebar.title("🃏 Poker Lounge")
user_name = st.sidebar.text_input("Your Name", placeholder="Enter name to join...")

if is_admin_route:
    st.sidebar.divider()
    st.sidebar.subheader("Admin Access")
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd == ADMIN_PASSWORD:
        authenticated = True
        st.sidebar.success("Admin Unlocked")
    elif pwd:
        st.sidebar.error("Incorrect Password")

# --- MAIN UI ---
st.title("Pointing Poker")

if not user_name:
    st.info("👈 Please enter your name in the sidebar to enter the voting room.")
    st.stop()

# Admin Controls
if authenticated:
    st.subheader("Admin Dashboard")
    col1, col2 = st.columns(2)
    if col1.button("🔓 Reveal Scores", use_container_width=True):
        data["revealed"] = True
        save_data(data)
        st.rerun()
    if col2.button("🔄 Reset Table", use_container_width=True):
        save_data({"votes": {}, "revealed": False})
        st.rerun()
    st.divider()

# Voting Cards
st.write(f"### Select your estimate, {user_name}:")
cards = ["1", "2", "3", "5", "8", "13", "21", "☕"]
cols = st.columns(len(cards))

for i, card in enumerate(cards):
    if cols[i].button(card, key=f"card_{card}"):
        data["votes"][user_name] = card
        save_data(data)
        st.toast(f"Vote cast: {card}")

# Results Section
st.divider()
if data["revealed"]:
    st.subheader("Final Results")
    if data["votes"]:
        # Create table
        df = pd.DataFrame(list(data["votes"].items()), columns=["Team Member", "Estimate"])
        st.table(df)
        
        # Stats calculation
        numeric_votes = [int(v) for v in data["votes"].values() if v.isdigit()]
        if numeric_votes:
            avg_val = sum(numeric_votes) / len(numeric_votes)
            st.metric("Average Score", f"{avg_val:.1f}")
    else:
        st.warning("The admin revealed the scores, but no one voted!")
else:
    st.subheader("The Table")
    if data["votes"]:
        # Show status grid of who has voted
        voter_cols = st.columns(4)
        for idx, player in enumerate(data["votes"].keys()):
            with voter_cols[idx % 4]:
                st.success(f"✅ {player}")
    else:
        st.write("Waiting for the first vote to be cast...")

# --- AUTO-REFRESH ---
# Keeps the UI synced across different users' browsers
time.sleep(2)
st.rerun()