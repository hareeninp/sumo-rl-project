from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_lane_vehicle_count,
    get_lane_mean_speed,
    get_queue_length
)

sumocfg = "simulation.sumocfg"

start_sim(sumocfg)

lane = "A0A1_0"

for i in range(60):

    step()

    vehicles = get_lane_vehicle_count(lane)
    speed = get_lane_mean_speed(lane)
    queue = get_queue_length(lane)

    print(
        f"Step: {i + 1:2d} | "
        f"Lane: {lane} | "
        f"Vehicles: {vehicles} | "
        f"Mean speed: {speed:.2f} | "
        f"Queue: {queue}"
    )

close_sim()
