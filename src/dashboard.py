"""
Streamlit Dashboard for Golem (Group F) vs Vampire (Group E).
Auto-refreshes every 5 seconds.
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
    page_title="Golem Ecosystem",
    page_icon="🪨",
    layout="wide",
)

st.title("🪨 Golem Population Model (vs Vampire)")


# --- API Helper Functions ---

def fetch_state() -> dict | None:
    """Fetch current state from API."""
    try:
        # Tries to get the last known state
        resp = requests.get(f"{API_URL}/simulation/state", timeout=1)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fetch_history() -> list:
    """Fetch simulation history from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/history", timeout=1)
        if resp.status_code == 200:
            data = resp.json()
            # Support both list directly or {"history": [...]} format
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
        st.warning(f"Could not run step: {e}")
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

    # 2. Display Metrics (Top Row)
    if state:
        col1, col2, col3 = st.columns(3)

        # Robust key handling: try "taille" (model output) or fallback to 0
        golem_current = state.get("taille", state.get("populations", {}).get("Golem", 0))
        
        # Robust key handling for rival: "vampire" (model output)
        vampire_current = state.get("vampire", state.get("populations", {}).get("Vampire", 0))
        
        # Robust key handling for time: "temps" or "time_step"
        time_current = state.get("temps", state.get("time_step", 0))

        with col1:
            st.metric(
                "🪨 Golem",
                f"{golem_current:.1f}",
                delta="Population Size"
            )

        with col2:
            st.metric(
                "🧛 Vampire",
                f"{vampire_current:.1f}",
                delta="Rival Species"
            )

        with col3:
            st.metric(
                "⏱️ Time Step",
                f"{time_current:.0f}",
            )

        st.divider()

    # 3. Control Buttons
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("▶️ Run 1 Step", use_container_width=True):
            if run_step():
                st.success("Step executed!")
                time.sleep(0.1)
                st.rerun()

    with col_b:
        if st.button("⏩ Run 50 Steps", use_container_width=True):
            progress_bar = st.progress(0)
            for i in range(50):
                run_step()
                progress_bar.progress((i + 1) / 50)
            st.success("50 steps executed!")
            st.rerun()

    with col_c:
        if st.button("🔄 Reset", use_container_width=True):
            if reset_simulation():
                st.info("Simulation reset!")
                st.rerun()

    st.divider()

    # 4. Visualization & History
    if history:
        # Transform API history list into a DataFrame for Plotly
        data_rows = []
        for record in history:
            # Handle keys: model.py uses 'temps', 'taille', 'vampire'
            t = record.get("temps", record.get("time", 0))
            g_pop = record.get("taille", record.get("populations", {}).get("Golem", 0))
            v_pop = record.get("vampire", record.get("populations", {}).get("Vampire", 0))
            
            # Golem Row
            data_rows.append({
                "Time": t,
                "Species": "Golem",
                "Population": g_pop
            })
            
            # Vampire Row (Handle negative cosine values by converting to NaN for graph)
            v_plot = v_pop if v_pop > 0 else np.nan
            data_rows.append({
                "Time": t,
                "Species": "Vampire",
                "Population": v_plot
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
            template="plotly_white"
        )
        
        fig.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # -- Statistics --
        st.subheader("📊 Statistics")
        
        # Calculate stats ignoring NaNs
        stats = df.groupby("Species")["Population"].agg(["min", "max", "mean", "std"])
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🪨 Golem Stats")
            if "Golem" in stats.index:
                row = stats.loc["Golem"]
                st.write(f"**Mean:** {row['mean']:.2f} | **Max:** {row['max']:.2f}")
                
        with c2:
            st.markdown("### 🧛 Vampire Stats")
            if "Vampire" in stats.index:
                row = stats.loc["Vampire"]
                st.write(f"**Mean:** {row['mean']:.2f} | **Max:** {row['max']:.2f}")

        with st.expander("View Raw Data"):
            st.dataframe(df)

    else:
        st.info("No history available. Click 'Run' to start simulation.")


# --- Auto-Refresh Logic ---
# Sleeps for 5 seconds, runs a step, then reloads the page.
time.sleep(REFRESH_INTERVAL)
run_step()
st.rerun()