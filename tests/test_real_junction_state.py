import traci
from traci_interface import start_sim, step, close_sim, get_junction_state

start_sim("network.sumocfg")

# Real junctions and their incoming lanes
junctions = {
    "J1": [
        "HOME1_J1_0",
        "HOSP1_J1_0",
        "J2_J1_0",
        "J2_J1_1",
        "J6_J1_0",
        "J6_J1_1"
    ],

    "J2": [
        "J12_J2_0",
        "J12_J2_1",
        "J16_J2_0",
        "J16_J2_1",
        "J1_J2_0",
        "J1_J2_1",
        "J3_J2_0",
        "J3_J2_1",
        "J7_J2_0",
        "J7_J2_1"
    ],

    "J3": [
        "HOSP2_J3_0",
        "J16_J3_0",
        "J16_J3_1",
        "J2_J3_0",
        "J2_J3_1",
        "J4_J3_0",
        "J4_J3_1",
        "J8_J3_0",
        "J8_J3_1"
    ]
}

for _ in range(5):
    step()

    print("\n==============================")
    print("Simulation Step")
    print("==============================")

    for junction_id, lanes in junctions.items():

        state = get_junction_state(
            junction_id,
            junction_id,
            lanes
        )

        print(f"\n{junction_id}")
        print(state)

close_sim()
