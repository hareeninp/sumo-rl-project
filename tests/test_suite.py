import traci

from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_junction_state,
    get_vehicle_position,
    get_vehicle_speed,
    get_vehicle_edge
)

from config import INCOMING_LANES


SUMO_CONFIG = "simulation.sumocfg"

JUNCTION_ID = "A1"

TLS_ID = None

VEHICLE_ID = "flow1.0"


start_sim(SUMO_CONFIG)

print("\n===== A2 TRACI TEST =====\n")


for i in range(10):

    step()

    print(f"--- Step {i + 1} ---")

    # -----------------------------
    # Junction state
    # -----------------------------

    state = get_junction_state(
        JUNCTION_ID,
        TLS_ID,
        INCOMING_LANES[JUNCTION_ID]
    )

    print("Junction State:")
    print(state)

    # -----------------------------
    # Vehicle state
    # -----------------------------

    vehicles = traci.vehicle.getIDList()

    if VEHICLE_ID in vehicles:

        position = get_vehicle_position(VEHICLE_ID)
        speed = get_vehicle_speed(VEHICLE_ID)
        edge = get_vehicle_edge(VEHICLE_ID)

        print("\nVehicle:")
        print("ID:", VEHICLE_ID)
        print("Position:", position)
        print("Speed:", speed)
        print("Edge:", edge)

    else:

        print("\nEmergency vehicle not currently active.")

    print()


close_sim()

print("===== TEST COMPLETE =====")
