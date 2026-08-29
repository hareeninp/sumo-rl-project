import traci
from traci_interface import start_sim, force_phase_change

start_sim("Network/network.sumocfg")

for i in range(10):
    traci.simulationStep()

print("Initial phase:", traci.trafficlight.getPhase("J1"))

force_phase_change("J1", 2)
print("After 0 -> 2:", traci.trafficlight.getPhase("J1"))

# Now test reverse transition
force_phase_change("J1", 0)
print("After 2 -> 0:", traci.trafficlight.getPhase("J1"))

traci.close()
