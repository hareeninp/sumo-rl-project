import traci
from traci_interface import start_sim, close_sim

start_sim("network.sumocfg")

junctions = [
    "J1", "J2", "J3", "J4",
    "J5", "J6", "J7", "J8",
    "J9", "J10", "J11", "J12",
    "J13", "J14", "J15", "J16"
]

all_lanes = traci.lane.getIDList()

for junction in junctions:

    incoming = []

    for lane in all_lanes:

        if lane.startswith(":"):
            continue

        parts = lane.rsplit("_", 1)

        if len(parts) != 2:
            continue

        edge_id = parts[0]

        if edge_id.endswith("_" + junction):
            incoming.append(lane)

    print("\n" + junction)
    print("Incoming lanes:")

    for lane in incoming:
        print("   ", lane)

close_sim()
