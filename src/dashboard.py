"""
Streamlit Dashboard for Golem (Group F) vs Vampire (Group E).
Includes Network Status Indicator, Auto-Refresh, and Robust Data Parsing.
"""

import time
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# --- Configuration ---
API_URL = "http://localhost:16050"
REFRESH_INTERVAL = 5  # seconds

# --- Page Config ---
st.set_page_config(
    page_title="Golem Population Model",
    page_icon="🪨",
    layout="wide",
)

st.title("🪨 Golem Population Model (vs Vampire)")


# --- API Helper Functions ---

def fetch_state() -> dict | None:
    """Fetch current state from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/state", timeout=1)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/styles/style.css")

def fetch_history() -> list:
    """Fetch simulation history from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/history", timeout=1)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("history", [])
    except Exception:
        pass
    return []

def run_step() -> bool:
    """Run one simulation step."""
    try:
        resp = requests.post(f"{API_URL}/simulation/step", timeout=1)
        return resp.status_code == 200
    except Exception as e:
        return False

def reset_simulation() -> bool:
    """Reset simulation."""
    try:
        resp = requests.post(f"{API_URL}/simulation/reset", timeout=1)
        return resp.status_code == 200
    except Exception:
        return False


# --- Main Dashboard Layout ---
placeholder = st.empty()

with placeholder.container():
    
    # 1. Fetch Data
    state = fetch_state()
    history = fetch_history()

    # 2. Network Status Indicator
    if state:
        is_connected = state.get("connected", False)
        if is_connected:
            st.success("🟢 **Network Status:** CONNECTED to Group E (Vampire API)")
        else:
            st.warning("🟠 **Network Status:** OFFLINE (Using Internal Simulation)")
    else:
        st.error("🔴 **System Status:** API Unreachable (Check Docker)")

    st.divider()

    # 3. Display Metrics (Top Row)
    if state:
        col1, col2, col3 = st.columns(3)

        # Robust extraction for current metrics
        pops = state.get("populations", {})
        golem_val = pops.get("Golem", state.get("taille", 0))
        vampire_val = pops.get("Vampire", state.get("vampire", 0))
        time_val = state.get("time_step", state.get("temps", 0))

        with col1:
            st.metric("🪨 Golem Population", f"{golem_val:.1f}")

        with col2:
            st.metric("🧛 Vampire Population", f"{vampire_val:.1f}")

        with col3:
            st.metric("⏱️ Time Step", f"{time_val:.0f}")

    # 4. Control Buttons
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("▶️ Run 1 Step", use_container_width=True):
            run_step()
            st.rerun()

    with col_b:
        if st.button("⏩ Run 50 Steps", use_container_width=True):
            progress_bar = st.progress(0)
            for i in range(50):
                run_step()
                progress_bar.progress((i + 1) / 50)
            st.rerun()

    with col_c:
        if st.button("🔄 Reset Simulation", use_container_width=True):
            reset_simulation()
            st.rerun()

    st.divider()

    # 5. Visualization & History (FIXED)
    if history:
        # Convert API history list to DataFrame
        data_rows = []
        for record in history:
            # 1. Get Time
            t = record.get("time", record.get("temps", 0))
            
            # 2. Extract Populations (Handle both nested and flat formats)
            # The database.py returns a 'populations' dictionary: {'Golem': 100, 'Vampire': 50}
            pops = record.get("populations", {})
            
            # Try getting from 'populations' dict FIRST, then fallback to flat keys
            g_pop = pops.get("Golem", record.get("taille", record.get("golem_population", 0)))
            v_pop = pops.get("Vampire", record.get("vampire", record.get("vampire_population", 0)))
            
            # 3. Append Golem Data
            data_rows.append({
                "Time": t,
                "Species": "Golem",
                "Population": g_pop
            })
            
            # 4. Append Vampire Data
            data_rows.append({
                "Time": t,
                "Species": "Vampire",
                "Population": v_pop
            })

        df = pd.DataFrame(data_rows)

        # -- Graph --
        st.subheader("📈 Population Dynamics")
        
        fig = px.line(
            df,
            x="Time",
            y="Population",
            color="Species",
            markers=True,
            color_discrete_map={"Golem": "#2E86C1", "Vampire": "#C0392B"},
            template="plotly_white",
            title="Lotka-Volterra Competition Model"
        )
        
        fig.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # -- Statistics --
        st.subheader("📊 Statistics")
        
        # Group by Species to get stats
        stats = df.groupby("Species")["Population"].agg(["min", "max", "mean", "std"])
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🪨 Golem Stats")
            if "Golem" in stats.index:
                row = stats.loc["Golem"]
                st.info(f"**Max:** {row['max']:.1f} | **Avg:** {row['mean']:.1f}")
                
        with c2:
            st.markdown("### 🧛 Vampire Stats")
            if "Vampire" in stats.index:
                row = stats.loc["Vampire"]
                st.info(f"**Max:** {row['max']:.1f} | **Avg:** {row['mean']:.1f}")

        with st.expander("View Raw Data Table"):
            st.dataframe(df, use_container_width=True)

    else:
        st.info("No simulation history yet. Click 'Run' to start.")


# --- Auto-Refresh Logic ---
# Sleep briefly then rerun to create the "live" effect
time.sleep(REFRESH_INTERVAL)
run_step()  # Automatically advance simulation
st.rerun()