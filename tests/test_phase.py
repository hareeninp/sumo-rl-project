import traci

traci.start([
    "sumo",
    "-c",
    "Network/network.sumocfg"
])

for step in range(100):
    traci.simulationStep()

    phase = traci.trafficlight.getPhase("J1")

    print(f"Step {step + 1}: J1 phase = {phase}")

traci.close()
