import traci

traci.start([
    "sumo",
    "-c",
    "Network/cfg_multi_ev.sumocfg"
])

for step in range(100):
    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()

    ambulances = [
        v for v in vehicles
        if "ambulance" in v.lower()
    ]

    print(f"\nStep {step + 1}")
    print("Ambulances:", ambulances)

    for ev in ambulances:
        print(
            ev,
            "position =", traci.vehicle.getPosition(ev),
            "speed =", traci.vehicle.getSpeed(ev),
            "edge =", traci.vehicle.getRoadID(ev)
        )

traci.close()
