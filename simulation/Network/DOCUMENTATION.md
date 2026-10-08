# Network Documentation — Member A1 Handover (Updated)

Covers the complete, current state of the network: base topology, hospitals, homes, fire/police/shopping facilities, the full emergency vehicle fleet, and TLS configuration exports.

## Files in this package

### Network core
| File | Purpose |
|---|---|
| `network.net.xml` | Compiled network — junctions, edges, traffic light logic (16 signals + facility spurs) |
| `network.nod.xml` / `network.edg.xml` | Source node/edge definitions — edit these + rerun netconvert to regenerate the network |
| `poi.add.xml` | Visual color-coded markers for every facility (see legend below) — load via `--additional-files` |

### Demand / scenario files
| File | Purpose |
|---|---|
| `network.rou.xml` | Baseline scenario — light background traffic + 1 test EV |
| `network_heavy.rou.xml` | Scenario variant 1 — heavy traffic across all routes |
| `network_specialist_jam.rou.xml` | Scenario variant 2 — HOSP2 (specialist) route congested, HOSP3 (general) route clear |
| `network_multi_ev.rou.xml` | Full emergency fleet scenario — 4 ambulances, 3 fire trucks, 2 police cars + background traffic (see below) |

### Run configs
| File | Pairs with |
|---|---|
| `network.sumocfg` | `network.rou.xml` |
| `cfg_heavy.sumocfg` | `network_heavy.rou.xml` |
| `cfg_specialist.sumocfg` | `network_specialist_jam.rou.xml` |
| `cfg_multi_ev.sumocfg` | `network_multi_ev.rou.xml` + `poi.add.xml` |

### Control & verification
| File | Purpose |
|---|---|
| `test_traci_control.py` | Proof that signals are externally controllable via TraCI (setRedYellowGreenState) |
| `watch_vehicles.py` | Terminal-only live vehicle tracker — no GUI needed, prints position/speed of every EV each step |

### TLS configuration (for Member B — RL agent)
| File | Purpose |
|---|---|
| `TLS_CONFIG_SUMMARY.md` | Human-readable per-junction phase breakdown, transition sequences, safe transition paths |
| `tls_full_config.json` | Machine-readable: full phase data + green-phase→movement mapping + safe green→green transition paths |
| `tls_phases.csv` | One row per phase: junction, index, classification, duration, state string |
| `tls_green_movements.csv` | One row per controlled movement per green phase (edge/lane/direction/priority) |
| `tls_safe_transitions.csv` | Explicit safe path (intermediate phases) between every pair of green phases, per junction |

**Note:** J5 has only 1 phase (permanent green) — it's a 2-way bend (J4↔J5↔J10) with no crossing traffic, not a network gap. Recommend Member B excludes it from the RL action space (or treats it as fixed/no-op).

## Junction reference (16 signal-controlled intersections)

| ID | x | y | Type |
|---|---|---|---|
| J1 | -600 | 300 | traffic_light |
| J2 | -300 | 450 | traffic_light |
| J3 | 0 | 450 | traffic_light |
| J4 | 300 | 400 | traffic_light |
| J5 | 600 | 300 | traffic_light |
| J6 | -600 | 0 | traffic_light |
| J7 | -300 | 0 | traffic_light |
| J8 | 0 | 0 | traffic_light |
| J9 | 300 | 0 | traffic_light |
| J10 | 600 | 0 | traffic_light |
| J11 | -600 | -300 | traffic_light |
| J12 | -300 | -400 | traffic_light |
| J13 | 0 | -450 | traffic_light |
| J14 | 300 | -350 | traffic_light |
| J15 | 600 | -300 | traffic_light |
| J16 | 0 | -150 | traffic_light |

## Destination / origin / facility nodes

| ID | x | y | Role | POI marker color |
|---|---|---|---|---|
| HOSP1 | -600 | 480 | Hospital (Cardio) | red |
| HOSP2 | 0 | 630 | Hospital (Specialized) | red |
| HOSP3 | 330 | 200 | Hospital (General) | red |
| HOSP4 | 150 | -620 | Hospital (Other Specialized) | red |
| FIRE1 | -300 | 150 | Fire Station | orange |
| POLICE1 | -750 | -150 | Police Station | blue |
| SHOP1 | 450 | 150 | Shopping Complex | purple |
| HOME1 | -780 | 300 | Home / trip origin | green |
| HOME2 | -780 | 0 | Home / trip origin | green |
| HOME3 | -780 | -300 | Home / trip origin | green |
| HOME4 | -150 | -620 | Home / trip origin | green |
| HOME5 | 780 | -300 | Home / trip origin | green |
| HOME6 | 780 | 0 | Home / trip origin | green |

**How facilities are marked:** two layers — (1) ID naming convention (HOSP/HOME/FIRE/POLICE/SHOP prefixes), and (2) visual POI color markers rendered on top of the network in sumo-gui via `poi.add.xml` (red=hospitals, orange=fire station, blue=police station, purple=shopping complex, green=homes). Load POIs with: `sumo-gui -n network.net.xml -a poi.add.xml -r <routefile>`, or they're already included automatically via `cfg_multi_ev.sumocfg`.

## Route IDs and what they represent

| Route ID | From -> To | Path |
|---|---|---|
| h1_hosp3_A/B/C | HOME1 -> HOSP3 (General) | 3 alternate paths via J2/J6/J7 corridors |
| h3_hosp2_A/B/C | HOME3 -> HOSP2 (Specialized) | 3 alternate paths via J6/J12 corridors |
| h6_hosp1_A/B/C | HOME6 -> HOSP1 (Cardio) | 3 alternate paths via J5/J9/J8 corridors |
| h5_hosp4_A/B/C | HOME5 -> HOSP4 (Other Specialized) | 3 alternate paths via J14/J12/J8 corridors |

## Scenario variant summary

| Scenario | File | Behavior |
|---|---|---|
| Baseline | network.rou.xml | Light background traffic (~150 veh/hr per route), 1 EV |
| Heavy traffic | network_heavy.rou.xml | ~600+ veh/hr across all routes; avg speed drops from 6.5 to 3.8 m/s |
| Specialist-jam | network_specialist_jam.rou.xml | HOSP2 routes saturated (500 veh/hr), HOSP3 route stays clear (60 veh/hr); tests EV routing under asymmetric congestion |
| Multi-EV fleet | network_multi_ev.rou.xml | Full emergency fleet + background traffic, POI markers included |

## Emergency vehicle fleet (network_multi_ev.rou.xml)

| Type | Count | Color | guiShape | Origin |
|---|---|---|---|---|
| Ambulance | 4 | red (1,0,0) | emergency | Various homes -> various hospitals, staggered departs (30/90/150/210s) |
| Fire truck | 3 | orange (1,0.4,0) | firebrigade | All dispatched from FIRE1 to different incident locations |
| Police car | 2 | blue (0,0,1) | police | Both dispatched from POLICE1 |

## TraCI control confirmation

Verified via `test_traci_control.py`: all tested junctions (J1, J8, J16) accept
`traci.trafficlight.setRedYellowGreenState()` overrides successfully. RL agent (Member B)
can control any of the 16 signals using:

```python
traci.trafficlight.setRedYellowGreenState(junction_id, state_string)
# or
traci.trafficlight.setPhase(junction_id, phase_index)
```

See `TLS_CONFIG_SUMMARY.md` and `tls_safe_transitions.csv` for the exact valid phase indices, state strings, and safe transition paths per junction before overriding.
