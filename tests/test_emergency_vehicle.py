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

emergency_vehicle = None

for i in range(20):

    step()

    vehicles = traci.vehicle.getIDList()

    # Select the first available vehicle as our dummy emergency vehicle
    if emergency_vehicle is None and len(vehicles) > 0:
        emergency_vehicle = vehicles[0]
        print("\nEmergency vehicle assigned:", emergency_vehicle)

    if emergency_vehicle is not None:

        # Check that the vehicle still exists
        if emergency_vehicle in traci.vehicle.getIDList():

            position = get_vehicle_position(emergency_vehicle)
            speed = get_vehicle_speed(emergency_vehicle)
            edge = get_vehicle_edge(emergency_vehicle)

            print(
                f"Step: {i + 1} | "
                f"Emergency Vehicle: {emergency_vehicle} | "
                f"Position: {position} | "
                f"Speed: {speed} | "
                f"Edge: {edge}"
            )

        else:
            print("Emergency vehicle has left the simulation.")
            break

close_sim()
