import traci

from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_junction_state
)

SUMO_CONFIG = "simulation.sumocfg"

start_sim(SUMO_CONFIG)

junction_id = "A1"

incoming_lanes = [
    "A0A1_0",
    "B1A1_0"
]

for i in range(5):
    step()

    state = get_junction_state(
        junction_id,
        None,
        incoming_lanes
    )

    print("\nStep:", i + 1)
    print(state)

close_sim()
