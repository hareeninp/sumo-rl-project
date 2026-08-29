import traci


# ============================================================
# SAFETY CONFIGURATION
# ============================================================

MIN_ACTION_INTERVAL = 5

last_change_time = {}


# ============================================================
# SIMULATION CONTROL
# ============================================================

def start_sim(sumocfg_path):
    traci.start(["sumo", "-c", sumocfg_path])


def step():
    traci.simulationStep()


def close_sim():
    traci.close()


# ============================================================
# LANE INFORMATION
# ============================================================

def get_lane_vehicle_count(lane_id):
    return traci.lane.getLastStepVehicleNumber(lane_id)


def get_lane_mean_speed(lane_id):
    return traci.lane.getLastStepMeanSpeed(lane_id)


def get_queue_length(lane_id):
    return traci.lane.getLastStepHaltingNumber(lane_id)


# ============================================================
# TRAFFIC SIGNAL INFORMATION
# ============================================================

def get_signal_phase(tls_id):
    return traci.trafficlight.getPhase(tls_id)


def set_signal_phase(tls_id, phase_id):

    current_time = traci.simulation.getTime()

    if not can_change_phase(tls_id, current_time):
        return False

    traci.trafficlight.setPhase(tls_id, phase_id)

    last_change_time[tls_id] = current_time

    return True


def can_change_phase(tls_id, current_time):

    last_time = last_change_time.get(tls_id, -999)

    return current_time - last_time >= MIN_ACTION_INTERVAL


def force_phase_change(tls_id, target_phase):
    """
    Safely move a traffic light from its current phase
    to the requested target phase.

    The function follows the phases already defined by SUMO.
    It does not jump directly between incompatible green phases.
    """

    current_phase = traci.trafficlight.getPhase(tls_id)

    if current_phase == target_phase:
        print(f"{tls_id}: already at phase {target_phase}")
        return

    # Get the complete TLS program
    logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]

    phases = logic.phases
    num_phases = len(phases)

    if target_phase < 0 or target_phase >= num_phases:
        raise ValueError(
            f"Invalid target phase {target_phase} for {tls_id}. "
            f"Valid phases: 0-{num_phases - 1}"
        )

    print(
        f"{tls_id}: changing phase "
        f"{current_phase} -> {target_phase}"
    )

    # Move through intermediate phases instead of jumping directly.
    phase = current_phase

    while phase != target_phase:

        phase = (phase + 1) % num_phases

        traci.trafficlight.setPhase(tls_id, phase)

        print(f"{tls_id}: entered phase {phase}")

        # Allow the phase to execute for its configured duration.
        duration = phases[phase].duration

        steps = max(1, int(round(duration)))

        for _ in range(steps):
            traci.simulationStep()

    current_time = traci.simulation.getTime()
    last_change_time[tls_id] = current_time

    print(
        f"{tls_id}: safely reached phase {target_phase}"
    )

# ============================================================
# VEHICLE INFORMATION
# ============================================================

def get_vehicle_position(vehicle_id):
    return traci.vehicle.getPosition(vehicle_id)


def get_vehicle_speed(vehicle_id):
    return traci.vehicle.getSpeed(vehicle_id)


def get_vehicle_edge(vehicle_id):
    return traci.vehicle.getRoadID(vehicle_id)


# ============================================================
# JUNCTION STATE
# ============================================================

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
            get_queue_length(lane_id)
        )

        state["vehicle_counts"][lane_id] = (
            get_lane_vehicle_count(lane_id)
        )

        state["mean_speeds"][lane_id] = (
            get_lane_mean_speed(lane_id)
        )

    # Get traffic-light phase if this junction has a TLS
    if tls_id is not None:

        state["current_phase"] = (
            get_signal_phase(tls_id)
        )

    return state
