from main import run_simulation
import streamlit as st
import yaml
import matplotlib.pyplot as plt
from pathlib import Path
import copy

st.set_page_config(layout="wide")
st.title("Baja Suspension Solver")

# Year selection
year = st.selectbox(
    "Select a year to run simulation",
    ("2021", "2024", "2026"),
    index=None,
    placeholder="Year",
)

if year is None:
    st.stop()

config_path = Path("hardpoints") / f"{year}.yml"

if not config_path.exists():
    st.error(f"Config file not found: {config_path}")
    st.stop()


# Load base config
with open("sim_config.yml") as file:
    base_config = yaml.safe_load(file)

base_config["HARDPOINTS"] = year

st.success(f"Loaded configuration: {config_path.name}")


# Cached simulation
@st.cache_data(show_spinner=True)
def run_cached_simulation(config: dict, year: str, half: str):
    return run_simulation(config)


# Tabs
tab_front, tab_rear = st.tabs(["Front", "Rear"])

def run_tab(half: str):
    config = copy.deepcopy(base_config)
    config["HALF"] = half

    result = run_cached_simulation(config, year, half)

    if not result["figures"]:
        st.warning("No plots generated for this configuration.")
        return

    for fig in result["figures"]:
        st.pyplot(fig)
        plt.close(fig)


# Tab contents
with tab_front:
    st.subheader("Front Suspension")
    run_tab("front")

with tab_rear:
    st.subheader("Rear Suspension")
    run_tab("rear")