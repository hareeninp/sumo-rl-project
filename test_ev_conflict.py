import traci

from traci_interface.traci_interface import (
    start_sim,
    step,
    close_sim,
    get_all_active_evs,
    get_ev_state
)

start_sim("A1_network/cfg_multi_ev.sumocfg")

TARGET_JUNCTION = "J8"

try:
    for i in range(300):
        step()

        active_evs = get_all_active_evs()
        near_junction = []

        for ev_id in active_evs:
            state = get_ev_state(ev_id)

            edge = state.get("current_edge")

            if edge and TARGET_JUNCTION in edge:
                near_junction.append((ev_id, state))

        if len(near_junction) >= 2:
            print()
            print("=== EV CONFLICT DETECTED ===")
            print("Simulation step:", i)
            print("Junction:", TARGET_JUNCTION)

            for ev_id, state in near_junction:
                print(
                    f"{ev_id}: "
                    f"phase={state['phase']}, "
                    f"priority={state['priority_weight']}, "
                    f"edge={state['current_edge']}"
                )

            break

    else:
        print()
        print("No natural EV conflict found in 300 steps.")

finally:
    close_sim()
