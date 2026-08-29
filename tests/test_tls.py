from traci_interface import (
    start_sim,
    step,
    close_sim,
    get_signal_phase
)


SUMO_CONFIG = "tls_test/tls.sumocfg"

start_sim(SUMO_CONFIG)

tls_id = "J"

for i in range(10):
    step()

    phase = get_signal_phase(tls_id)

    print(
        "Step:", i + 1,
        "| Traffic Light:", tls_id,
        "| Phase:", phase
    )

close_sim()
