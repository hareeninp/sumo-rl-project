from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_lane_vehicle_count,
    get_lane_mean_speed,
    get_queue_length
)


SUMO_CONFIG = "simulation.sumocfg"

start_sim(SUMO_CONFIG)

lane_id = "A0A1_0"

for i in range(10):
    step()

    vehicle_count = get_lane_vehicle_count(lane_id)
    speed = get_lane_mean_speed(lane_id)
    queue = get_queue_length(lane_id)
    print(
        "Step:", i + 1,
        "| Lane:", lane_id,
        "| Vehicles:", vehicle_count,
        "| Mean speed:", speed,
        "| Queue:", queue
    )

close_sim()
