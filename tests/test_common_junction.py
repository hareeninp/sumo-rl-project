import traci

SUMO_CONFIG = "../Network/cfg_multi_ev.sumocfg"

traci.start([
    "sumo",
    "-c",
    SUMO_CONFIG
])

print("=" * 60)
print("TC5 - Emergency Vehicles Reaching Common Junction")
print("=" * 60)

vehicles = {
    "ambulance_1",
    "ambulance_2"
}

common_edges = {
    "J4_J9",
    "J4_J3",
    "J3_J4",
    "J3_J2"
}

detected = set()
common_junction_seen = set()

for step in range(300):

    traci.simulationStep()

    for vehicle_id in vehicles:

        if vehicle_id not in traci.vehicle.getIDList():
            continue

        detected.add(vehicle_id)

        edge = traci.vehicle.getRoadID(vehicle_id)
        speed = traci.vehicle.getSpeed(vehicle_id)

        if edge in common_edges:
            if vehicle_id not in common_junction_seen:
                print(
                    f"Step {step}: {vehicle_id} reached "
                    f"common junction area | Edge: {edge}"
                )

            common_junction_seen.add(vehicle_id)

traci.close()

print("\nDetected:", detected)
print("Common junction area reached:", common_junction_seen)

assert detected == vehicles, \
    "Both ambulances were not detected"

assert len(common_junction_seen) >= 1, \
    "No ambulance reached the common junction area"
print("\nTC5 PASSED")
