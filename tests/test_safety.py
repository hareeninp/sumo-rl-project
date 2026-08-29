from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_signal_phase,
    set_signal_phase,
    can_change_phase
)

SUMO_CONFIG = "tls_test/tls.sumocfg"

start_sim(SUMO_CONFIG)

tls_id = "J"

step()

print("Time: 1")
print("Can change:", can_change_phase(tls_id, 1))

set_signal_phase(tls_id, 2)

print("Changed to phase:", get_signal_phase(tls_id))

print("Time: 2")
print("Can change:", can_change_phase(tls_id, 2))

print("Time: 7")
print("Can change:", can_change_phase(tls_id, 7))

close_sim()
