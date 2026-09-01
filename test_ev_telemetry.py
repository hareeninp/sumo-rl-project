import traci

traci.start([
    "sumo",
    "-c",
    "A1_network/network.sumocfg"
])

print("TRACKING EV_1")

while traci.simulation.getMinExpectedNumber() > 0:

    traci.simulationStep()

    if "ev_1" in traci.vehicle.getIDList():

        edge = traci.vehicle.getRoadID("ev_1")
        position = traci.vehicle.getLanePosition("ev_1")
        speed = traci.vehicle.getSpeed("ev_1")

        print(
            f"TIME={traci.simulation.getTime():.0f} "
            f"EDGE={edge} "
            f"POS={position:.1f} "
            f"SPEED={speed:.1f}"
        )

traci.close()
