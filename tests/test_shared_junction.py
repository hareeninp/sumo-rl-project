import traci

SUMO_CONFIG = "../Network/cfg_multi_ev.sumocfg"

traci.start([
    "sumo",
    "-c",
    SUMO_CONFIG
])

print("=" * 60)
print("TC4 - Multiple Emergency Vehicles / Shared Junction Test")
print("=" * 60)

target_vehicles = {
    "ambulance_1",
    "ambulance_2",
    "firetruck_1",
    "police_1"
}

detected = set()

for step in range(180):

    traci.simulationStep()

    active = traci.vehicle.getIDList()

    for vehicle_id in active:

        if vehicle_id in target_vehicles:

            edge = traci.vehicle.getRoadID(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)

            if vehicle_id not in detected:
                print(
                    f"Detected: {vehicle_id} | "
                    f"Edge: {edge} | "
                    f"Speed: {speed:.2f}"
                )
                detected.add(vehicle_id)

            assert edge != "", (
                f"{vehicle_id} has no current edge"
            )

            assert speed >= 0, (
                f"{vehicle_id} has invalid speed"
            )

traci.close()

print("\nDetected vehicles:")
for vehicle_id in sorted(detected):
    print(" ", vehicle_id)

assert detected == target_vehicles, (
    "Not all target emergency vehicles were detected"
)

print("\nTC4 PASSED")

