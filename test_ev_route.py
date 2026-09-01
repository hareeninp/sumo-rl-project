import traci

traci.start(["sumo", "-c", "../Network/network.sumocfg"])

last = None
print("TRACKING EV_1")

for _ in range(600):
    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()

    if "ev_1" in vehicles:
        edge = traci.vehicle.getRoadID("ev_1")

        if edge != last:
            print(
                "TIME:",
                traci.simulation.getTime(),
                "EDGE:",
                edge
            )
            last = edge

    elif traci.simulation.getTime() > 60:
        print("EV FINISHED")
        break

traci.close()
