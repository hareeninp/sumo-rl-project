import traci

SUMO_CONFIG = "../Network/cfg_multi_ev.sumocfg"

traci.start([
    "sumo",
    "-c",
    SUMO_CONFIG
])

print("=" * 55)
print("TC2 - Two Ambulances Active/Tracked Test")
print("=" * 55)

ambulances = {"ambulance_1", "ambulance_2"}
detected = set()

for step in range(150):

    traci.simulationStep()

    active_ambulances = set(traci.vehicle.getIDList()) & ambulances

    if active_ambulances:
        for ambulance_id in active_ambulances:

            if ambulance_id not in detected:
                print(
                    f"Detected: {ambulance_id} | "
                    f"Step: {step}"
                )
                detected.add(ambulance_id)

            speed = traci.vehicle.getSpeed(ambulance_id)
            edge = traci.vehicle.getRoadID(ambulance_id)

            print(
                f"Step {step}: "
                f"{ambulance_id} | "
                f"Speed: {speed:.2f} | "
                f"Edge: {edge}"
            )

traci.close()

print("\nAmbulances detected:", detected)

assert "ambulance_1" in detected, "ambulance_1 was not detected"
assert "ambulance_2" in detected, "ambulance_2 was not detected"

print("\nTC2 PASSED")
