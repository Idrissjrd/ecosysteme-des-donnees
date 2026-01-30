"""
Streamlit Dashboard with auto-refresh (5s) and population visualization.
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

st.title("Golem Population Model")


def fetch_state() -> dict | None:
    """Fetch current state from API."""
    try:
        resp = requests.get(f"{API_URL}/simulation/state", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.warning(f"API error: {e}")
    return None

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/styles/style.css")


def fetch_population() -> dict | None:
    """Fetch current population from API."""
    try:
        resp = requests.get(f"{API_URL}/population/taille", timeout=2)
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
            return data.get("history", [])
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


def reset_simulation() -> bool:
    """Reset simulation."""
    try:
        resp = requests.post(f"{API_URL}/simulation/reset", timeout=2)
        return resp.status_code == 200
    except Exception as e:
        st.warning(f"Could not reset: {e}")
        return False


# Main dashboard layout
placeholder = st.empty()

with placeholder.container():
    # Current metrics
    state = fetch_state()
    pop_data = fetch_population()

    if state and pop_data:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Golem",
                f"{pop_data['taille']:.1f}",
                delta=f"t={state['time_step']}",
            )

        with col2:
            # Get vampire population from last history entry (DISPLAY ONLY)
            history = fetch_history()
            vampire_pop = 0
            if history:
                vampire_pop = history[-1].get("vampire_population", 0)

            # Affichage uniquement au-dessus de 0 (sans changer les données)
            vampire_pop_display = vampire_pop if vampire_pop > 0 else 0

            st.metric(
                "Vampire",
                f"{vampire_pop_display:.1f}",
                delta=f"t={state['time_step']}",
            )

        with col3:
            st.metric(
                "Time Step",
                state["time_step"],
            )

        st.divider()

    notification_container = st.empty()

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Run 1 Step", use_container_width=True):
            if run_step():
                notification_container.success("Step executed!")
                time.sleep(2)
                notification_container.empty()
                st.rerun()

    with col_b:
        if st.button("Run 50 Steps", use_container_width=True):
            p_bar_container = st.empty()
            for i in range(50):
                run_step()
            notification_container.success("50 steps executed!")
            time.sleep(2)
            notification_container.empty()
            p_bar_container.empty()
            st.rerun()

    with col_c:
        if st.button("Reset", use_container_width=True):
            if reset_simulation():
                notification_container.info("Simulation reset!")
                time.sleep(2)
                notification_container.empty()
                st.rerun()

    st.divider()
    # History and visualization
    history = fetch_history()

    if history:
        # Prepare data from history
        data = []
        for record in history:
            t = record["time_step"]
            golem_pop = record["golem_population"]
            vampire_pop = record.get("vampire_population", 0)

            # --- CHANGE D'AFFICHAGE ICI ---
            # On remplace les valeurs négatives par NaN pour que Plotly ne les trace pas.
            vampire_plot_value = vampire_pop if vampire_pop > 0 else np.nan

            data.append(
                {
                    "Time": t,
                    "Species": "Golem",
                    "Population": golem_pop,
                }
            )

            data.append(
                {
                    "Time": t,
                    "Species": "Vampire",
                    "Population": vampire_plot_value,
                }
            )

        df = pd.DataFrame(data)

        # Plot population evolution
        st.subheader("Population Evolution (Lotka-Volterra Model)")

        fig = px.line(
            df,
            x="Time",
            y="Population",
            color="Species",
            title="Population Dynamics Over Time",
            markers=True,
            template="plotly_white",
            labels={"Time": "Time Step (t)", "Population": "Population Size N(t)"},
            color_discrete_map={"Golem": "#32B48E", "Vampire": "#E6817E"},
        )

        fig.update_layout(
            hovermode="x unified",
            height=500,
            xaxis_title="Time Step (t)",
            yaxis_title="Population Size N(t)",
        )

        # Force l'axe Y à démarrer à 0 (optionnel mais cohérent avec ">=0")
        fig.update_yaxes(rangemode="tozero")

        # Add carrying capacity line
        fig.add_hline(
            y=1000,
            line_dash="dot",
            line_color="gray",
            annotation_text="K = 1000",
            annotation_position="right",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Statistics (sur les valeurs affichées pour Vampire)
        st.subheader("Statistics")

        stats = df.groupby("Species")["Population"].agg(["min", "max", "mean", "std"])

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Golem Statistics**")
            if "Golem" in stats.index:
                golem_stats = stats.loc["Golem"]
                st.metric("Min", f"{golem_stats['min']:.2f}")
                st.metric("Max", f"{golem_stats['max']:.2f}")
                st.metric("Mean", f"{golem_stats['mean']:.2f}")
                if pd.notna(golem_stats["std"]) and golem_stats["std"] > 0:
                    st.metric("Std Dev", f"{golem_stats['std']:.2f}")

        with col2:
            st.write("**Vampire Statistics (values > 0 only)**")
            if "Vampire" in stats.index:
                vampire_stats = stats.loc["Vampire"]
                # min peut être NaN si toutes les valeurs sont <= 0
                if pd.isna(vampire_stats["min"]):
                    st.info("Aucune valeur Vampire > 0 pour l'instant.")
                else:
                    st.metric("Min", f"{vampire_stats['min']:.2f}")
                    st.metric("Max", f"{vampire_stats['max']:.2f}")
                    st.metric("Mean", f"{vampire_stats['mean']:.2f}")
                    if pd.notna(vampire_stats["std"]) and vampire_stats["std"] > 0:
                        st.metric("Std Dev", f"{vampire_stats['std']:.2f}")

        # Raw data
        with st.expander("Raw Data"):
            st.dataframe(df, use_container_width=True)

    else:
        st.info("No data yet. Run some simulation steps!")


# Auto-refresh mechanism - runs step automatically every 5 seconds
time.sleep(REFRESH_INTERVAL)
run_step()
st.rerun()