# default
import time
from typing import Dict, Tuple, List
import yaml
import matplotlib.pyplot as plt

# third party
import numpy as np

# ours
from models.hardpoints import Vehicle, DoubleAArm, SemiTrailingLink
from scripts.utils.plotter import (
    PlotterBase,
    DoubleAArmPlotter,
    SemiTrailingLinkPlotter,
    CharacteristicPlotter,
    AxleCharacteristicsPlotter,
    AXLE_CHARACTERISTIC,
    SCALAR_CHARACTERISTIC,
)
from scripts.simulation import (
    Simulation, 
    WheelAttitudeSimulation, 
    JackingSimulation
)
from scripts.utils.wheel_utils import wheel_attitude

CORNER_MAP = {
    ("left", "front"):  "front_left",
    ("right", "front"): "front_right",
    ("left", "rear"):   "rear_left",
    ("right", "rear"):  "rear_right",
}

def run_simulation(config: Dict) -> Dict[str, object]:

    hp_file = f"hardpoints/{config['HARDPOINTS']}.yml"
    with open(hp_file, 'r') as file:
        data = yaml.safe_load(file)

    vehicle: Vehicle = Vehicle(data)

    # Which corner are we simulating?
    side = config.get("SIDE", "right") # default to right
    half = config.get("HALF", "front") # default to front
    corner = getattr(vehicle, CORNER_MAP[(side, half)])

    # Pick simulation
    if config['SIMULATION'] == 'wheel_attitude':
        simulation = WheelAttitudeSimulation(vehicle, config)
        steps = simulation.run(corner=corner)
    elif config['SIMULATION'] == 'jacking':
        simulation = JackingSimulation(vehicle, config)
        steps = simulation.run(half=half)
    else:
        raise ValueError("SIMULATION must be 'wheel_attitude' or 'jacking'.")

    # Create and populate plots
    plots: List[PlotterBase] = []
    if config["PLOTS"]["CAMBER"]:
        plots.append(CharacteristicPlotter(SCALAR_CHARACTERISTIC.CAMBER))
    if config["PLOTS"]["CASTER"] and half == 'front':
        plots.append(CharacteristicPlotter(SCALAR_CHARACTERISTIC.CASTER))
    if config["PLOTS"]["TOE"]:
        plots.append(CharacteristicPlotter(SCALAR_CHARACTERISTIC.TOE))

    if config["PLOTS"].get("AXLE_PLUNGE", False):
        plots.append(AxleCharacteristicsPlotter(AXLE_CHARACTERISTIC.PLUNGE))
    if config["PLOTS"].get("AXLE_ANGLES", False):
        plots.append(AxleCharacteristicsPlotter(AXLE_CHARACTERISTIC.ANGLE_IB))
        plots.append(AxleCharacteristicsPlotter(AXLE_CHARACTERISTIC.ANGLE_OB))

    if config["PLOTS"].get("3D", False):
        hp = corner.hardpoints
        if half == 'front' and isinstance(hp, DoubleAArm):
            plots.append(DoubleAArmPlotter(hp))
        elif half == 'rear' and isinstance(hp, SemiTrailingLink):
            plots.append(SemiTrailingLinkPlotter(hp))

    # Update 2D plots across steps
    for step in steps:
        att = wheel_attitude(step)
        att["travel_mm"] = step["travel_mm"]   # ✅ REQUIRED

        for plot in plots:
            if isinstance(plot, CharacteristicPlotter):
                plot.update(att)
            else:
                plot.update(step)

    return {
        "steps": steps,
        "figures": [p.get_figure() for p in plots],
    }

# CLI - optional
if __name__ == "__main__":
    with open("sim_config.yml", "r") as file:
        config = yaml.safe_load(file)

    result = run_simulation(config)
    plt.show()