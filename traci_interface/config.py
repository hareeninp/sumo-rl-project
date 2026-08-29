# Junction IDs
JUNCTION_IDS = [
    "A0",
    "A1",
    "B0",
    "B1"
]

# Incoming lanes for each junction
INCOMING_LANES = {
    "A0": [
        "A1A0_0",
        "B0A0_0"
    ],

    "A1": [
        "A0A1_0",
        "B1A1_0"
    ],

    "B0": [
        "A0B0_0",
        "B1B0_0"
    ],

    "B1": [
        "A1B1_0",
        "B0B1_0"
    ]
}

# Traffic-light IDs
TLS_IDS = {
    # Currently these are placeholders because
    # the present network has priority junctions.
    "A0": None,
    "A1": None,
    "B0": None,
    "B1": None
}

# Emergency vehicle
EMERGENCY_VEHICLE_ID = "flow1.0"
