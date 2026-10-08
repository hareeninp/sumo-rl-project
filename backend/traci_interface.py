import traci

MIN_ACTION_INTERVAL = 5

last_change_time = {}


def start_sim(sumocfg_path):
    traci.start(["sumo", "-c", sumocfg_path])


def step():
    traci.simulationStep()


def close_sim():
    traci.close()


def get_lane_vehicle_count(lane_id):
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_mean_speed(lane_id):
    return traci.lane.getLastStepMeanSpeed(lane_id)


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


def get_signal_phase(tls_id):
    return traci.trafficlight.getPhase(tls_id)


def set_signal_phase(tls_id, phase_id):
    traci.trafficlight.setPhase(tls_id, phase_id)

    current_time = traci.simulation.getTime()
    last_change_time[tls_id] = current_time


def can_change_phase(tls_id, current_time):
    last_time = last_change_time.get(tls_id, -999)

    return current_time - last_time >= MIN_ACTION_INTERVAL


def force_phase_change(tls_id, target_phase):
    current_phase = traci.trafficlight.getPhase(tls_id)

    # Already at requested phase
    if current_phase == target_phase:
        return

    # Move through the defined intermediate phases
    # instead of directly jumping to another green phase.

    if target_phase > current_phase:

        for phase in range(current_phase + 1, target_phase + 1):

            traci.trafficlight.setPhase(tls_id, phase)

            print(
                f"{tls_id}: entered phase {phase}"
            )

            traci.simulationStep()

    else:

        # Wrap around to phase 0
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]

        num_phases = len(logic.phases)

        for phase in range(current_phase + 1, num_phases):

            traci.trafficlight.setPhase(tls_id, phase)

            print(
                f"{tls_id}: entered phase {phase}"
            )

            traci.simulationStep()

        for phase in range(0, target_phase + 1):

            traci.trafficlight.setPhase(tls_id, phase)

            print(
                f"{tls_id}: entered phase {phase}"
            )

            traci.simulationStep()

    print(
        f"{tls_id}: safely reached phase {target_phase}"
    )


def get_vehicle_position(vehicle_id):
    return traci.vehicle.getPosition(vehicle_id)


def get_vehicle_speed(vehicle_id):
    return traci.vehicle.getSpeed(vehicle_id)


def get_vehicle_edge(vehicle_id):
    return traci.vehicle.getRoadID(vehicle_id)


def get_junction_state(junction_id, tls_id, lanes):

    state = {
        "junction_id": junction_id,
        "queue_lengths": {},
        "vehicle_counts": {},
        "mean_speeds": {},
        "current_phase": None
    }

    for lane_id in lanes:

        state["queue_lengths"][lane_id] = (
            traci.lane.getLastStepHaltingNumber(lane_id)
        )

        state["vehicle_counts"][lane_id] = (
            traci.lane.getLastStepVehicleNumber(lane_id)
        )

        state["mean_speeds"][lane_id] = (
            traci.lane.getLastStepMeanSpeed(lane_id)
        )

    # Get traffic-light phase if this junction has a TLS
    if tls_id is not None:

        state["current_phase"] = (
            traci.trafficlight.getPhase(tls_id)
        )

    return state