# TraCI Interface — A1 Handoff Specification

**Module:** `traci_interface/traci_interface.py`
**Audience:** B1
**Status:** Confirmed interface, based on implemented functions and observed test results only. Anything not explicitly verified by testing is marked as an assumption.

---

## 1. Purpose

This document specifies the public interface exposed by `traci_interface.py` for interacting with the SUMO simulation. It exists so that B1 can integrate against a stable, documented contract rather than reading A1's internal implementation (the EV registry, TraCI calls, or internal state-tracking logic).

**B1 must use these interface functions instead of calling raw TraCI APIs or accessing internal data structures (e.g. `ev_registry`) directly.** The internal implementation is not part of this contract and may change without notice; only the functions listed below are guaranteed.

---

## 2. Simulation Control

### `start_sim(sumocfg_path)`
- **Purpose:** Starts a SUMO simulation using the given `.sumocfg` file.
- **Signature:** `start_sim(sumocfg_path: str) -> None`
- **Return value:** None (confirmed).
- **Behavior:** Verified working with `cfg_multi_ev.sumocfg`. B1 should call this before any other simulation-dependent function.

### `step()`
- **Purpose:** Advances the simulation by one step.
- **Signature:** `step() -> None`
- **Return value:** None (confirmed).
- **Behavior:** Underlies all observed test results (EV phase transitions, junction conflicts, etc.), so it is confirmed functional, but its return value/side effects beyond advancing simulation time are not separately documented here.

### `close_sim()`
- **Purpose:** Closes/terminates the running SUMO simulation.
- **Signature:** `close_sim() -> None`
- **Return value:** None (assumed based on naming; not explicitly covered in test notes).

---

## 3. Emergency Vehicle Registration and State

### `register_ev(vehicle_id, vehicle_type="ambulance", phase="dispatch", target=None, priority_class=2.5)`
- **Purpose:** Registers a vehicle as an emergency vehicle (EV) with type, phase, target, and priority.
- **Signature:** `register_ev(vehicle_id: str, vehicle_type: str = "ambulance", phase: str = "dispatch", target=None, priority_class: float = 2.5) -> None` (return type assumed; not explicitly tested)
- **Behavior:** Defaults confirmed by function signature. Tested EVs (`ambulance_1`, `firetruck_1`, `police_1`) all registered with `priority_weight = 2.5`.

### `update_ev_phase_automatically(vehicle_id)`
- **Purpose:** Automatically updates an EV's phase based on simulation state (e.g. proximity to target).
- **Signature:** `update_ev_phase_automatically(vehicle_id: str) -> None` (return type assumed)
- **Confirmed behavior:** A dispatch → transport transition was observed when `ambulance_1` reached its target edge `J9_HOSP3` at simulation time 279. This confirms the automatic phase transition works for at least this case; broader transition logic (e.g. transport → other phases) is not confirmed by the provided tests.

### `update_ev_phase(vehicle_id, phase)`
- **Purpose:** Manually sets an EV's phase.
- **Signature:** `update_ev_phase(vehicle_id: str, phase: str) -> None` (return type assumed; not explicitly tested)
- **Note:** Valid phase values are not enumerated in the provided material beyond `"dispatch"` and `"transport"`. B1 should not assume other phase strings are supported without confirming with A1.

### `get_ev_priority(vehicle_id)`
- **Purpose:** Returns the priority weight of a registered EV.
- **Signature:** `get_ev_priority(vehicle_id: str) -> float` (assumed return type, consistent with `priority_weight` field)
- **Confirmed behavior:** All three tested EVs returned `2.5`.

### `get_ev_state(vehicle_id)`
- **Purpose:** Returns the full state of a registered EV.
- **Signature:** `get_ev_state(vehicle_id: str) -> dict`
- **Return value (confirmed fields):**
  ```python
  {
      "vehicle_id": str,
      "active": bool,        # type assumed
      "type": str,
      "phase": str,
      "condition": None,     # confirmed None during tested dispatch state
      "target": str | None,
      "priority_weight": float,
      "position": tuple,     # type assumed, consistent with get_vehicle_position
      "speed": float,        # type assumed, consistent with get_vehicle_speed
      "current_edge": str,
  }
  ```
- **Important:** `condition` was observed as `None` during the tested dispatch phase. Whether it takes other values in other phases is **not confirmed** — B1 must not assume `condition` is always populated.

### `log_specialty_gap(vehicle_id, required_specialty, selected_hospital)`
- **Purpose:** Logs a mismatch between a required medical specialty and the hospital selected for an EV.
- **Signature:** `log_specialty_gap(vehicle_id: str, required_specialty: str, selected_hospital: str) -> None` (return type assumed; not covered in test notes)
- **Note:** No test evidence was provided for this function's behavior. Treat as declared-but-unverified.

### `is_emergency_vehicle(vehicle_id)`
- **Purpose:** Checks whether a given vehicle ID is registered as an EV.
- **Signature:** `is_emergency_vehicle(vehicle_id: str) -> bool` (assumed return type)

### `get_all_active_evs()`
- **Purpose:** Returns all currently active/registered EVs.
- **Signature:** `get_all_active_evs() -> list`
- **Confirmed behavior:** Returned `ambulance_1`, `firetruck_1`, `police_1` in testing, including simultaneously during the J8 multi-EV conflict — both `firetruck_1` and `police_1` remained independently accessible with correct priority (2.5) at the same time.

### `get_emergency_vehicle_state(vehicle_id="ev_1")`
- **Purpose:** Returns EV state, appears to be an alternate/related accessor to `get_ev_state`.
- **Signature:** `get_emergency_vehicle_state(vehicle_id: str = "ev_1") -> dict` (return shape assumed to mirror `get_ev_state`; not separately confirmed by test notes)
- **Important:** The relationship between this function and `get_ev_state` (identical, overlapping, or distinct data) is **not confirmed**. B1 should confirm with A1 before relying on both interchangeably.

### `get_emergency_vehicle_junction(vehicle_id="ev_1")`
- **Purpose:** Returns the junction associated with/nearest to a given EV.
- **Signature:** `get_emergency_vehicle_junction(vehicle_id: str = "ev_1") -> str | None` (assumed return type; not explicitly covered in test notes)

---

## 4. Junction and Traffic State

### `get_lane_vehicle_count(lane_id)`
- **Purpose:** Returns the number of vehicles currently on a lane.
- **Signature:** `get_lane_vehicle_count(lane_id: str) -> int` (assumed return type)

### `get_lane_mean_speed(lane_id)`
- **Purpose:** Returns the mean speed of vehicles on a lane.
- **Signature:** `get_lane_mean_speed(lane_id: str) -> float` (assumed return type)

### `get_queue_length(lane_id)`
- **Purpose:** Returns the queue length on a lane.
- **Signature:** `get_queue_length(lane_id: str) -> int | float` (assumed return type)

### `get_junction_state(junction_id, tls_id, lanes)`
- **Purpose:** Returns aggregated state for a junction, including queue/vehicle/speed data per lane and current signal phase.
- **Signature:** `get_junction_state(junction_id: str, tls_id: str | None, lanes: list) -> dict`
- **Return value (confirmed fields):**
  ```python
  {
      "junction_id": str,
      "queue_lengths": dict,   # or list, per-lane — exact structure not specified
      "vehicle_counts": dict,
      "mean_speeds": dict,
      "current_phase": int | None,
  }
  ```
- **Confirmed edge case:** `TLS_IDS` currently contains `None` for the configured junctions in the test setup, so `current_phase=None` is **expected**, not an error, for these junctions. B1 must handle `current_phase is None` as a normal case, not a failure.
- **Confirmed:** State classification into LOW/MEDIUM/HIGH, queue totals, and RL-state construction from this data passed testing.

---

## 5. Signal Control

### `get_signal_phase(tls_id)`
- **Purpose:** Returns the current phase of a traffic light system (TLS).
- **Signature:** `get_signal_phase(tls_id: str) -> int | None` (assumed return type)
- **Note:** Given the `current_phase=None` behavior confirmed under section 4, B1 should expect `None` for junctions without a configured TLS here as well, though this specific function was not separately called out in the test notes.

### `set_signal_phase(tls_id, phase_id)`
- **Purpose:** Sets the phase of a TLS.
- **Signature:** `set_signal_phase(tls_id: str, phase_id: int) -> None` (return type assumed; not covered in test notes)
- **Note:** No test evidence was provided confirming this function's effect on the simulation. Do not assume signal-control behavior beyond what testing shows (see Section 9).

### `can_change_phase(tls_id, current_time)`
- **Purpose:** Checks whether a TLS phase change is permitted at the given simulation time (e.g. respecting minimum phase duration).
- **Signature:** `can_change_phase(tls_id: str, current_time: float) -> bool` (assumed return type)
- **Note:** Not explicitly covered in test notes. Timing/threshold logic is unconfirmed.

### `force_phase_change(tls_id, target_phase)`
- **Purpose:** Forces an immediate TLS phase change, bypassing normal timing checks.
- **Signature:** `force_phase_change(tls_id: str, target_phase: int) -> None` (return type assumed; not covered in test notes)

**Important:** Signal-control functions (`set_signal_phase`, `can_change_phase`, `force_phase_change`) are declared in the interface but their effects are **not shown as validated by the provided tests**. B1 should treat these as functionally present but not confirmed end-to-end, and coordinate with A1 before depending on specific signal-control outcomes.

---

## 6. Routing and Vehicle Telemetry

### `get_route_to_target(vehicle_id, target_edge_id)`
- **Purpose:** Computes a route and travel time from a vehicle's current position to a target edge.
- **Signature:** `get_route_to_target(vehicle_id: str, target_edge_id: str) -> tuple[list, float]`
- **Confirmed behavior:**
  - Valid call: `get_route_to_target("ambulance_1", "J9_HOSP3")` returned a valid route and travel time.
  - **Invalid target edge:** returns `([], inf)`.
- **Edge case B1 must handle:** Always check for an empty route list and/or `inf` travel time before using the result — do not assume a route was found.

### `get_vehicle_position(vehicle_id)`
- **Purpose:** Returns a vehicle's current position.
- **Signature:** `get_vehicle_position(vehicle_id: str) -> tuple` (assumed coordinate format, e.g. `(x, y)`)

### `get_vehicle_speed(vehicle_id)`
- **Purpose:** Returns a vehicle's current speed.
- **Signature:** `get_vehicle_speed(vehicle_id: str) -> float` (assumed return type)

### `get_vehicle_edge(vehicle_id)`
- **Purpose:** Returns the edge a vehicle is currently on.
- **Signature:** `get_vehicle_edge(vehicle_id: str) -> str` (assumed return type)

### `get_vehicle_ids()`
- **Purpose:** Returns all vehicle IDs currently present in the simulation.
- **Signature:** `get_vehicle_ids() -> list` (assumed return type)

**Confirmed (telemetry, aggregate):** Route/telemetry tracking successfully followed an EV through multiple edges until route completion, exercising position/edge/speed-style tracking over time.

---

## 7. Utility Functions

### `get_simulation_time()`
- **Purpose:** Returns the current simulation time.
- **Signature:** `get_simulation_time() -> float`
- **Confirmed behavior:** Used to timestamp the observed dispatch → transport transition at time 279.

### `vehicle_exists(vehicle_id)`
- **Purpose:** Checks whether a given vehicle ID currently exists in the simulation.
- **Signature:** `vehicle_exists(vehicle_id: str) -> bool` (assumed return type)
- **Recommended use:** B1 should call this (or `is_emergency_vehicle`, as appropriate) before querying state for a vehicle ID that may have left the simulation, to avoid errors on invalid/expired IDs.

---

## 8. Return Value Specifications

| Function | Return type | Confirmed by test? |
|---|---|---|
| `get_ev_state` | `dict` (see §3 for fields) | Yes |
| `get_junction_state` | `dict` (see §4 for fields) | Yes |
| `get_route_to_target` | `tuple[list, float]`, `([], inf)` on invalid target | Yes |
| `get_all_active_evs` | `list` of vehicle IDs | Yes |
| `get_ev_priority` | `float` (`2.5` observed) | Yes |
| `get_simulation_time` | `float` | Yes (used for timestamping) |
| `get_signal_phase` / `current_phase` in `get_junction_state` | `int` or `None` | `None` case confirmed |
| All other functions listed in §2, §3, §5, §6, §7 not called out above | Return types are **assumed** from naming/context, not explicitly confirmed by test output | No |

---

## 9. Edge Cases / Important Constraints

- **Invalid route target:** `get_route_to_target()` may return `([], inf)`. B1 must check for this before using the route or travel time — do not assume a non-empty route.
- **Unconfigured TLS:** `current_phase` may be `None` when a junction has no configured TLS (`TLS_IDS` currently contains `None` for the tested junctions). This is expected, not an error condition.
- **`condition` field:** `condition` in `get_ev_state()` was `None` during the tested dispatch state. Its behavior in other phases is not confirmed.
- **Automatic phase transitions:** EV phase automatically changes from `dispatch` to `transport` when the EV reaches its configured target edge (confirmed once, for `ambulance_1` at time 279). Do not assume this generalizes to all phase transitions without further testing.
- **Multi-EV handling:** Multiple EVs (e.g. `firetruck_1` and `police_1` near junction J8) can be simultaneously and independently tracked in the registry, each with correct individual priority. B1 can rely on concurrent EV tracking for at least this scenario.
- **Signal control is not fully validated:** `set_signal_phase`, `can_change_phase`, and `force_phase_change` are part of the interface but their end-to-end effects on the simulation are **not shown as validated** by the provided tests. Do not assume complete, tested signal-control behavior — coordinate with A1 if B1's integration depends on this.
- **Internal state access is off-limits:** B1 must not read or modify `ev_registry` or call raw TraCI functions directly. All interaction should go through this interface.

---

## 10. Verified Test Results

The following have been directly observed passing in testing:

- SUMO simulation starts successfully using `cfg_multi_ev.sumocfg`.
- `get_all_active_evs()` correctly detects `ambulance_1`, `firetruck_1`, `police_1`.
- `get_ev_state()` returns all documented fields, including `condition=None` in the tested dispatch state.
- All three tested EVs report `priority_weight = 2.5`.
- `get_route_to_target("ambulance_1", "J9_HOSP3")` returns a valid route and travel time; an invalid target edge returns `([], inf)`.
- `get_junction_state()` returns all documented fields, with `current_phase=None` correctly reflecting unconfigured TLS junctions.
- Dispatch → transport phase transition observed for `ambulance_1` upon reaching `J9_HOSP3` at simulation time 279.
- Multi-EV conflict at junction J8 correctly tracked: `firetruck_1` and `police_1` simultaneously and independently registered, both with `priority_weight = 2.5`.
- State classification (LOW/MEDIUM/HIGH), queue totals, and RL-state construction all passed.
- Q-learning components passed: action space, action selection, Q-value update, epsilon decay, save/load.
- Telemetry/route tracking successfully followed an EV through multiple edges to route completion.

**Not claimed as validated:** full signal-control behavior (`set_signal_phase`, `can_change_phase`, `force_phase_change`), `log_specialty_gap`, and the exact relationship between `get_ev_state` and `get_emergency_vehicle_state`. These are present in the interface but should not be assumed fully tested end-to-end.

---

## 11. B1 Integration Rules

1. **Use this interface exclusively.** Do not access `ev_registry` or call raw TraCI functions directly.
2. **Always check `get_route_to_target()` output** for `([], inf)` before using route or travel-time data.
3. **Treat `current_phase=None` as a valid, expected state** for junctions without a configured TLS — do not treat it as an error.
4. **Do not assume `condition` is always populated** on EV state — it may be `None`, as observed in the tested dispatch phase.
5. **Do not assume full signal-control functionality is validated.** If B1's integration depends on `set_signal_phase`, `can_change_phase`, or `force_phase_change` behaving correctly end-to-end, confirm with A1 first.
6. **Confirm with A1 before relying on `get_emergency_vehicle_state`** as identical to `get_ev_state` — their exact relationship is not documented in the provided tests.
7. **Use `vehicle_exists()` / `is_emergency_vehicle()`** before querying state for vehicle IDs that may not currently exist in the simulation.
8. **Do not generalize the single confirmed dispatch → transport transition** to assume all EV phase transitions are automatic and validated.
