import traci

from traci_interface import start_sim, force_phase_change

start_sim("Network/network.sumocfg")

traci.simulationStep()

print("\n==============================")
print("Testing J4: Green 0 -> Green 3")
print("==============================")

print("Initial phase:", traci.trafficlight.getPhase("J4"))

force_phase_change("J4", 3)

print("Final phase:", traci.trafficlight.getPhase("J4"))

traci.close()
