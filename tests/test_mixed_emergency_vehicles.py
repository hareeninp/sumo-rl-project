import traci

SUMO_CONFIG = "../Network/cfg_multi_ev.sumocfg"

traci.start([
    "sumo",
    "-c",
    SUMO_CONFIG
])

print("=" * 60)
print("TC3 - Mixed Emergency Vehicle Tracking Test")
print("=" * 60)

expected = {
    "ambulance_1": "ambulance",
    "firetruck_1": "firetruck",
    "police_1": "policecar",
}

detected = set()

for step in range(120):

    traci.simulationStep()

    for vehicle_id in traci.vehicle.getIDList():

        if vehicle_id in expected:

            vehicle_type = traci.vehicle.getTypeID(vehicle_id)

            if vehicle_id not in detected:
                print(
                    f"Detected: {vehicle_id} | "
                    f"Type: {vehicle_type} | "
                    f"Step: {step}"
                )

                assert vehicle_type == expected[vehicle_id], (
                    f"Wrong type for {vehicle_id}: "
                    f"expected {expected[vehicle_id]}, "
                    f"got {vehicle_type}"
                )

                detected.add(vehicle_id)

            # Verify TraCI can read current state
            speed = traci.vehicle.getSpeed(vehicle_id)
            edge = traci.vehicle.getRoadID(vehicle_id)

            assert speed >= 0, (
                f"Invalid speed for {vehicle_id}"
            )

            assert edge != "", (
                f"No road information for {vehicle_id}"
            )

traci.close()

print("\nDetected:", detected)
print("Expected:", set(expected.keys()))

assert detected == set(expected.keys()), (
    "Not all emergency vehicle types were detected"
)

print("\nTC3 PASSED")
