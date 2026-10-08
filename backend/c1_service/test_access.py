from access import validate_hospital_access


result = validate_hospital_access(
    "H1",
    "H1"
)

print("Same hospital access:", result)


result = validate_hospital_access(
    "H1",
    "H2"
)

print("Cross-hospital access:", result)