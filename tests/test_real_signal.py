import traci
from traci_interface import start_sim, step, close_sim
from traci_interface import get_signal_phase, set_signal_phase

start_sim("network.sumocfg")

# Let simulation start
step()

for junction_id in ["J1", "J8", "J16"]:

    print("\n==============================")
    print("Junction:", junction_id)
    print("==============================")

    current_phase = get_signal_phase(junction_id)

    print("Current phase:", current_phase)

    # Try changing phase
    target_phase = 2

    print("Changing to phase:", target_phase)

    set_signal_phase(junction_id, target_phase)

    new_phase = get_signal_phase(junction_id)

    print("New phase:", new_phase)

close_sim()
