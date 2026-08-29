import traci
from traci_interface import (
    start_sim,
    close_sim,
    step,
    get_junction_state,
    get_signal_phase
)

SUMO_CONFIG = "network.sumocfg"

junctions = {
    "J1": {
        "tls": "J1",
        "lanes": [
            "HOME1_J1_0",
            "HOSP1_J1_0",
            "J2_J1_0",
            "J2_J1_1",
            "J6_J1_0",
            "J6_J1_1"
        ]
    },

    "J8": {
        "tls": "J8",
        "lanes": [
            "J13_J8_0",
            "J13_J8_1",
            "J16_J8_0",
            "J16_J8_1",
            "J3_J8_0",
            "J3_J8_1",
            "J6_J8_0",
            "J6_J8_1",
            "J7_J8_0",
            "J7_J8_1",
            "J9_J8_0",
            "J9_J8_1"
        ]
    },

    "J16": {
        "tls": "J16",
        "lanes": [
            "J11_J16_0",
            "J11_J16_1",
            "J13_J16_0",
            "J13_J16_1",
            "J2_J16_0",
            "J2_J16_1",
            "J3_J16_0",
            "J3_J16_1",
            "J8_J16_0",
            "J8_J16_1"
        ]
    },

    "J5": {
        "tls": None,
        "lanes": [
            "J10_J5_0",
            "J10_J5_1",
            "J4_J5_0",
            "J4_J5_1"
        ]
    },

    "J12": {
        "tls": "J12",
        "lanes": [
            "J11_J12_0",
            "J11_J12_1",
            "J13_J12_0",
            "J13_J12_1",
            "J15_J12_0",
            "J15_J12_1",
            "J2_J12_0",
            "J2_J12_1",
            "J7_J12_0",
            "J7_J12_1"
        ]
    }
}


start_sim(SUMO_CONFIG)

step()

for junction_id, config in junctions.items():

    print("\n==============================")
    print(f"Junction: {junction_id}")
    print("==============================")

    try:
        state = get_junction_state(
            junction_id,
            config["tls"],
            config["lanes"]
        )

        print("State:")
        print(state)

        if config["tls"] is not None:
            print("Signal phase:", get_signal_phase(config["tls"]))
        else:
            print("Signal phase: No traffic light")

    except Exception as e:
        print("ERROR:", e)

close_sim()
