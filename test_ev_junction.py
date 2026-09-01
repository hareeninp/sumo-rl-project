import traci

from traci_interface.traci_interface import (
    start_sim,
    step,
    close_sim,
    get_emergency_vehicle_junction,
    get_emergency_vehicle_state,
)

from traci_interface.config import EMERGENCY_VEHICLE_ID


SUMO_CONFIG = "A1_network/network.sumocfg"

start_sim(SUMO_CONFIG)

print("===== A2 EV JUNCTION TEST =====")
print(f"TRACKING {EMERGENCY_VEHICLE_ID}")

try:

    while traci.simulation.getMinExpectedNumber() > 0:

        step()

        if EMERGENCY_VEHICLE_ID in traci.vehicle.getIDList():

            state = get_emergency_vehicle_state(
                EMERGENCY_VEHICLE_ID
            )

            junction = get_emergency_vehicle_junction(
                EMERGENCY_VEHICLE_ID
            )

            print(
                f"TIME={traci.simulation.getTime():.0f} "
                f"EDGE={state['edge']} "
                f"POS={state['position']:.1f} "
                f"SPEED={state['speed']:.1f} "
                f"JUNCTION={junction}"
            )

finally:

    close_sim()

print("===== TEST COMPLETE =====")
