import traci

from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_lane_vehicle_count,
    get_lane_mean_speed,
    get_queue_length,
    get_vehicle_position,
    get_vehicle_speed,
    get_vehicle_edge,
    get_junction_state
)

SUMO_CONFIG = "Network/cfg_multi_ev.sumocfg"





start_sim(SUMO_CONFIG)

junction_id = "J1"

incoming_lanes = [
    "HOME1_J1_0",
    "HOSP1_J1_0",
    "J2_J1_0",
    "J2_J1_1",
    "J6_J1_0",
    "J6_J1_1"
]

for i in range(100):

    step()

    print("\n==============================")
    print("Simulation Step:", i + 1)
    print("==============================")

    # 1. Junction state
    state = get_junction_state(
        junction_id,
        None,
        incoming_lanes
    )

    print("Junction State:")
    print(state)

    # 2. Vehicle information
    vehicles = traci.vehicle.getIDList()

    if vehicles:
        vehicle_id = vehicles[0]

        print("\nVehicle:", vehicle_id)
        print("Position:", get_vehicle_position(vehicle_id))
        print("Speed:", get_vehicle_speed(vehicle_id))
        print("Edge:", get_vehicle_edge(vehicle_id))

close_sim()
