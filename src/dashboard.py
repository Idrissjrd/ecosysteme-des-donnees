"""
Streamlit Dashboard with auto-refresh (5s) and cosine wave visualization.
"""

import time
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Configuration
API_URL = "http://localhost:16050"
REFRESH_INTERVAL = 5  # seconds

# Page config
st.set_page_config(
    page_title="Golem Population Model",
    layout="wide",
)

st.title(" Golem Population Model" )



def fetch_state() -> dict | None:
    """Fetch current state from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/state", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"API error: {e}")
    return None


def fetch_history() -> list:
    """Fetch simulation history from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/history", timeout=2)
        if resp.status_code == 200:
            return resp.json().get("history", [])
    except Exception:
        pass
    return []


def run_step() -> bool:
    """Run one simulation step."""
    try:
        resp = requests.post(f"{API_URL}/simulation/step", timeout=2)
        return resp.status_code == 200
    except Exception as e:
        st.warning(f"Could not run step: {e}")
        return False


# Main dashboard layout
placeholder = st.empty()

with placeholder.container():
    # Current metrics
    state = fetch_state()
    if state:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                " Golem",
                f"{state['populations']['Golem']:.1f}",
                delta=f"t={state['time_step']}",
            )

        with col2:
            st.metric(
                " Human",
                f"{state['populations']['Human']:.1f}",
                delta=f"t={state['time_step']}",
            )

        with col3:
            st.metric(
                "⏱️ Time Step",
                state['time_step'],
            )

        st.divider()

    # Control buttons
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("▶️ Run 1 Step", use_container_width=True):
            if run_step():
                st.success("Step executed!")

    with col_b:
        if st.button("▶️ Run 10 Steps", use_container_width=True):
            progress_bar = st.progress(0)
            for i in range(10):
                run_step()
                progress_bar.progress((i + 1) / 10)
            st.success("10 steps executed!")

    with col_c:
        if st.button("🔄 Reset", use_container_width=True):
            try:
                requests.post(f"{API_URL}/simulation/reset", timeout=2)
                st.info("Simulation reset!")
            except Exception as e:
                st.error(f"Reset failed: {e}")

    st.divider()

    # History and visualization
    history = fetch_history()

    if history:
        # Prepare data from history
        data = []
        for record in history:
            t = record["time"]
            for species, pop in record["populations"].items():
                data.append(
                    {
                        "Time": t,
                        "Species": species,
                        "Population": pop,
                    }
                )

        df = pd.DataFrame(data)

        # Add cosine wave for reference
        times = sorted(df["Time"].unique())
        K = 1000
        omega = 0.1
        wave = K * np.cos(np.array(times) * omega) + K

        wave_df = pd.DataFrame(
            {
                "Time": times,
                "Species": "Golem (Cosine Wave Demo)",
                "Population": wave,
            }
        )

        df_combined = pd.concat([df, wave_df], ignore_index=True)

        # Plot population evolution
        st.subheader("📈 Population Evolution (Lotka-Volterra + Cosine Wave)")

        fig = px.line(
            df_combined,
            x="Time",
            y="Population",
            color="Species",
            title="Population Dynamics Over Time",
            markers=True,
            template="plotly_white",
            labels={"Time": "Time Step (t)", "Population": "Population Size N_i(t)"},
        )

        fig.update_layout(
            hovermode="x unified",
            height=500,
            xaxis_title="Time Step (t_n)",
            yaxis_title="Population Size (N_i)",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Statistics
        st.subheader("📊 Statistics")

        stats = df.groupby("Species")["Population"].agg(
            ["min", "max", "mean", "std"]
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Golem Statistics**")
            if "Golem" in stats.index:
                golem_stats = stats.loc["Golem"]
                st.metric("Min", f"{golem_stats['min']:.2f}")
                st.metric("Max", f"{golem_stats['max']:.2f}")
                st.metric("Mean", f"{golem_stats['mean']:.2f}")

        with col2:
            st.write("**Human Statistics**")
            if "Human" in stats.index:
                human_stats = stats.loc["Human"]
                st.metric("Min", f"{human_stats['min']:.2f}")
                st.metric("Max", f"{human_stats['max']:.2f}")
                st.metric("Mean", f"{human_stats['mean']:.2f}")

        # Raw data
        with st.expander("📋 Raw Data"):
            st.dataframe(df, use_container_width=True)

    else:
        st.info("No data yet. Run some simulation steps!")

# Auto-refresh mechanism
time.sleep(REFRESH_INTERVAL)
run_step()
st.rerun()
