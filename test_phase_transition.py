from traci_interface.traci_interface import *


from traci_interface.traci_interface import (
    start_sim,
    step,
    close_sim,
    register_ev,
    ev_registry,
    vehicle_exists,
    get_vehicle_edge,
    get_simulation_time,
    update_ev_phase_automatically
)
start_sim("A1_network/cfg_multi_ev.sumocfg")

register_ev("ambulance_1", target="J9_HOSP3")

print("Target:", ev_registry["ambulance_1"]["target"])
print("Initial phase:", ev_registry["ambulance_1"]["phase"])

for _ in range(350):
    step()

    if vehicle_exists("ambulance_1"):
        edge = get_vehicle_edge("ambulance_1")

        update_ev_phase_automatically("ambulance_1")

        phase = ev_registry["ambulance_1"]["phase"]

        # Print every 20 seconds and whenever the phase changes
        if int(get_simulation_time()) % 20 == 0 or phase == "transport":
            print(
                f"TIME={get_simulation_time():.0f} "
                f"EDGE={edge} "
                f"PHASE={phase}"
            )

        if phase == "transport":
            print("✅ DISPATCH -> TRANSPORT SUCCESS")
            break

else:
    print("❌ EV did not transition to transport.")

close_sim()
