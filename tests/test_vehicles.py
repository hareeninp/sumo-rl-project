import traci

from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_vehicle_position,
    get_vehicle_speed,
    get_vehicle_edge
)


SUMO_CONFIG = "simulation.sumocfg"

start_sim(SUMO_CONFIG)

for i in range(10):
    step()

    vehicles = traci.vehicle.getIDList()

    if len(vehicles) > 0:
        vehicle_id = vehicles[0]

        position = get_vehicle_position(vehicle_id)
        speed = get_vehicle_speed(vehicle_id)
        edge = get_vehicle_edge(vehicle_id)

        print(
            "Step:", i + 1,
            "| Vehicle:", vehicle_id,
            "| Position:", position,
            "| Speed:", speed,
            "| Edge:", edge
        )
    else:
        print("Step:", i + 1, "| No vehicles")

close_sim()
