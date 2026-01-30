"""
Streamlit Dashboard for Golem Population Model.
Optimized for data robustness and clear visualization.
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
    layout="wide",
)

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("assets/styles/style.css")

st.title("Golem Population Model")

# --- API Helper Functions ---

def fetch_state() -> dict | None:
    """Fetch current state from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/state", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fetch_history() -> list:
    """Fetch simulation history from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/history", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("history", [])
    except Exception:
        pass
    return []

def run_step() -> bool:
    """Run one simulation step."""
    try:
        resp = requests.post(f"{API_URL}/simulation/step", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

def reset_simulation() -> bool:
    """Reset simulation."""
    try:
        resp = requests.post(f"{API_URL}/simulation/reset", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

# --- Main Dashboard Layout ---
placeholder = st.empty()

with placeholder.container():
    state = fetch_state()
    history = fetch_history()

    # 1. Network Status Indicator (from New Version)
    if state:
        is_connected = state.get("connected", False)
        if is_connected:
            st.success("Network Status: CONNECTED to external API")
        else:
            st.warning("Network Status: OFFLINE (Internal Simulation)")
    else:
        st.error("System Status: API Unreachable (Check Docker/Server)")

    st.divider()

    # 2. Current Metrics
    if state:
        col1, col2, col3 = st.columns(3)
        
        # Robust data extraction
        pops = state.get("populations", {})
        golem_val = pops.get("Golem", state.get("taille", 0))
        vampire_val = pops.get("Vampire", state.get("vampire", 0))
        time_val = state.get("time_step", state.get("temps", 0))

        with col1:
            st.metric("Golem Population", f"{golem_val:.1f}")
        with col2:
            st.metric("Vampire Population", f"{max(0, vampire_val):.1f}")
        with col3:
            st.metric("Time Step", f"{time_val}")
        
        st.divider()

    # 3. Control Buttons
    notification_container = st.empty()
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Run 1 Step", use_container_width=True):
            if run_step():
                st.rerun()

    with col_b:
        if st.button("Run 50 Steps", use_container_width=True):
            for i in range(50):
                run_step()
            st.rerun()

    with col_c:
        if st.button("Reset Simulation", use_container_width=True):
            if reset_simulation():
                st.rerun()

    st.divider()

    # 4. Visualization & History
    if history:
        data_rows = []
        for record in history:
            t = record.get("time_step", record.get("time", record.get("temps", 0)))
            
            # Robust populations extraction
            pops = record.get("populations", {})
            g_pop = pops.get("Golem", record.get("golem_population", record.get("taille", 0)))
            v_pop = pops.get("Vampire", record.get("vampire_population", record.get("vampire", 0)))

            # Golem entry
            data_rows.append({"Time": t, "Species": "Golem", "Population": g_pop})
            
            # Vampire entry (NaN for negative values to break the line in Plotly)
            v_plot_val = v_pop if v_pop > 0 else np.nan
            data_rows.append({"Time": t, "Species": "Vampire", "Population": v_plot_val})

        df = pd.DataFrame(data_rows)

        st.subheader("Population Evolution (Lotka-Volterra Model)")
        
        fig = px.line(
            df,
            x="Time",
            y="Population",
            color="Species",
            markers=True,
            template="plotly_white",
            color_discrete_map={"Golem": "#32B48E", "Vampire": "#E6817E"}
        )
        
        fig.update_layout(height=500, hovermode="x unified")
        fig.update_yaxes(rangemode="tozero")
        
        # Carrying capacity indicator
        fig.add_hline(y=1000, line_dash="dot", line_color="gray", annotation_text="K = 1000")
        
        st.plotly_chart(fig, use_container_width=True)

        # 5. Statistics
        st.subheader("Statistics")
        stats = df.dropna(subset=["Population"]).groupby("Species")["Population"].agg(["min", "max", "mean", "std"])
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.write("**Golem Statistics**")
            if "Golem" in stats.index:
                row = stats.loc["Golem"]
                st.metric("Max", f"{row['max']:.2f}")
                st.metric("Mean", f"{row['mean']:.2f}")
                
        with s_col2:
            st.write("**Vampire Statistics (N > 0)**")
            if "Vampire" in stats.index:
                row = stats.loc["Vampire"]
                st.metric("Max", f"{row['max']:.2f}")
                st.metric("Mean", f"{row['mean']:.2f}")

        with st.expander("Raw Data Table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No history available. Run steps to generate data.")

# --- Auto-Refresh Logic ---
time.sleep(REFRESH_INTERVAL)
run_step()
st.rerun()