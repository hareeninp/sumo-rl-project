import traci

traci.start([
    "sumo",
    "-c",
    "Network/network.sumocfg"
])

traci.simulationStep()

current = traci.trafficlight.getPhase("J1")

print("Current phase:", current)

traci.trafficlight.setPhase("J1", 2)

new = traci.trafficlight.getPhase("J1")

print("Phase after change:", new)

traci.close()
