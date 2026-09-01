import traci

SUMO_CONFIG = "A1_network/cfg_multi_ev.sumocfg"

traci.start([
    "sumo",
    "-c",
    SUMO_CONFIG
])

print("=" * 50)
print("TC1 - Emergency Vehicle Detection Test")
print("=" * 50)

expected_vehicles = {
    "ambulance_1": "ambulance",
    "firetruck_1": "firetruck",
    "police_1": "policecar",
    "ambulance_2": "ambulance",
    "firetruck_2": "firetruck",
    "ambulance_3": "ambulance",
    "police_2": "policecar",
    "firetruck_3": "firetruck",
    "ambulance_4": "ambulance"
}

detected = set()

for step in range(300):

    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()

    for vehicle_id in vehicles:

        if vehicle_id in expected_vehicles and vehicle_id not in detected:

            vehicle_type = traci.vehicle.getTypeID(vehicle_id)

            print(
                f"Detected: {vehicle_id} | "
                f"Type: {vehicle_type} | "
                f"Step: {step}"
            )

            assert vehicle_type == expected_vehicles[vehicle_id], (
                f"Wrong type for {vehicle_id}: "
                f"expected {expected_vehicles[vehicle_id]}, "
                f"got {vehicle_type}"
            )

            detected.add(vehicle_id)

traci.close()

print("\nDetected vehicles:", len(detected))
print("Expected vehicles:", len(expected_vehicles))

assert detected == set(expected_vehicles.keys()), (
    "Some expected emergency vehicles were not detected"
)

print("\nTC1 PASSED")
