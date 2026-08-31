from rl_agent.team2.state import discretize_queue, get_total_queue, get_rl_state

print("=" * 60)
print("STATE TEST")
print("=" * 60)

# TC1: queue 0-4 -> LOW
assert discretize_queue(0) == 0
assert discretize_queue(4) == 0
print("TC1 PASSED - LOW")

# TC2: queue 5-9 -> MEDIUM
assert discretize_queue(5) == 1
assert discretize_queue(9) == 1
print("TC2 PASSED - MEDIUM")

# TC3: queue 10+ -> HIGH
assert discretize_queue(10) == 2
assert discretize_queue(15) == 2
print("TC3 PASSED - HIGH")

# TC4: total queue
state = {
    "queues": {
        "lane_N": 3,
        "lane_S": 2,
        "lane_E": 5,
        "lane_W": 4
    }
}

total = get_total_queue(
    state,
    ["lane_N", "lane_S", "lane_E", "lane_W"]
)

assert total == 14
print("TC4 PASSED - Total queue =", total)

# TC5: RL state
rl_state = get_rl_state(
    state,
    traffic_groups={
        "group_1": ["lane_N", "lane_S"],
        "group_2": ["lane_E", "lane_W"]
    },
    valid_green_phases=[0, 2]
)

print("RL State:", rl_state)

assert rl_state == (0, 1, 1)
print("TC5 PASSED - RL state")

print("\nALL STATE TESTS PASSED")
