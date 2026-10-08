# TLS Phase Configuration — Full Reference for Member B (RL Agent)

Extracted directly from `network.net.xml`. TLS id == Junction id in this network.

**Note on phase classification `mixed(green+yellow)`:** some junctions (e.g. J1 phase 1) have a phase where part of the intersection is yellow while another, non-conflicting part is still green. This is a legitimate SUMO-generated transitional phase at complex multi-leg junctions, not an error — treat it as belonging to the yellow/transition group for safety purposes.

**Note on J5:** only 1 phase, permanently green. J5 sits on a 2-way bend (J4↔J5↔J10) with no crossing traffic, so there is no real signal decision there — treat it as a fixed/no-op action space (action space size 1), not a bug.

## Per-junction overview

| Junction | Total Phases | Green Phase IDs | Yellow Phase IDs | All-Red Phase IDs | Controlled Links |
|---|---|---|---|---|---|
| J1 | 8 | [0, 2, 4, 6] | [3, 7] | [] | 18 |
| J2 | 14 | [0, 3, 6, 8, 11] | [1, 4, 7, 9, 12] | [2, 5, 10, 13] | 30 |
| J3 | 8 | [0, 2, 4, 6] | [1, 7] | [] | 29 |
| J4 | 8 | [0, 3, 5] | [1, 6] | [2, 7] | 20 |
| J5 | 1 | [0] | [] | [] | 4 |
| J6 | 12 | [0, 2, 4, 6, 8, 10] | [3, 7, 11] | [] | 40 |
| J7 | 12 | [0, 2, 4, 6, 8, 10] | [3, 7, 11] | [] | 42 |
| J8 | 12 | [0, 2, 4, 6, 8, 10] | [3, 7, 9, 11] | [] | 44 |
| J9 | 14 | [0, 2, 4, 6, 8, 10, 12] | [3, 7, 11, 13] | [] | 55 |
| J10 | 11 | [0, 2, 4, 6, 9] | [3, 7] | [8] | 29 |
| J11 | 8 | [0, 2, 5] | [3, 6] | [4, 7] | 18 |
| J12 | 14 | [0, 2, 5, 8, 11] | [3, 6, 9, 12] | [4, 7, 10, 13] | 30 |
| J13 | 12 | [0, 2, 4, 6, 8, 10] | [3, 7, 11] | [] | 40 |
| J14 | 4 | [0, 2] | [] | [] | 12 |
| J15 | 7 | [0, 3, 5] | [1, 6] | [2] | 19 |
| J16 | 10 | [0, 2, 5, 8] | [3, 6] | [4, 7] | 31 |

## Transition sequence

SUMO cycles phases strictly in the index order defined in `network.net.xml`, wrapping back to phase 0 after the last phase. This is the **fixed-time baseline sequence** — an RL agent overriding via TraCI (`setPhase`/`setRedYellowGreenState`) can jump to any phase index directly, but should still route green→yellow→(all-red)→green when switching to a *non-adjacent* green phase, to avoid an unsafe direct green-to-green flip across conflicting movements.

| Junction | Sequence (phase indices, in defined order, wraps to start) |
|---|---|
| J1 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 0 |
| J2 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 0 |
| J3 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 0 |
| J4 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 0 |
| J5 | 0 → 0 |
| J6 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 0 |
| J7 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 0 |
| J8 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 0 |
| J9 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 0 |
| J10 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 0 |
| J11 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 0 |
| J12 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 0 |
| J13 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 0 |
| J14 | 0 → 1 → 2 → 3 → 0 |
| J15 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 0 |
| J16 | 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 0 |

## Full phase detail per junction

### J1 (program `0`, 18 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 33 | `GGGggrrrrGGggrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyggrrrryyggrrrrr` |
| 2 | green | 6 | `rrrGGrrrrrrGGrrrrr` |
| 3 | yellow | 3 | `rrryyrrrrrryyrrrrr` |
| 4 | green | 33 | `rrrrrGGggrrrrGGGgg` |
| 5 | mixed(green+yellow) | 3 | `rrrrryyggrrrryyygg` |
| 6 | green | 6 | `rrrrrrrGGrrrrrrrGG` |
| 7 | yellow | 3 | `rrrrrrryyrrrrrrryy` |

### J2 (program `0`, 30 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 11 | `GGGGGgGrrrrrrrrrrrrrrrrrrrrrrr` |
| 1 | yellow | 3 | `yyyyyyyrrrrrrrrrrrrrrrrrrrrrrr` |
| 2 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 3 | green | 15 | `rrrrrrrrrrrrrrrrrrGGGGGgGrrrrr` |
| 4 | yellow | 3 | `rrrrrrrrrrrrrrrrrryyyyyyyrrrrr` |
| 5 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 6 | green | 15 | `GGrrrrrrrrrrrrrrrrrrrrrrGGGGGg` |
| 7 | yellow | 3 | `yyrrrrrrrrrrrrrrrrrrrrrryyyyyy` |
| 8 | green | 15 | `rrrrrrGGGGGgGrrrrrrrrrrrrrrrrr` |
| 9 | yellow | 3 | `rrrrrryyyyyyyrrrrrrrrrrrrrrrrr` |
| 10 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 11 | green | 15 | `rrrrrrrrrrrrGGGGGgrrrrGrrrrrrr` |
| 12 | yellow | 3 | `rrrrrrrrrrrryyyyyyrrrryrrrrrrr` |
| 13 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |

### J3 (program `0`, 29 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 24 | `rrrrrrrGGGgggrrrrrrrrrrGGGGgg` |
| 1 | yellow | 3 | `rrrrrrryyyyyyrrrrrrrrrryyyyyy` |
| 2 | green | 24 | `GGGggggrrrrrrrrrrrgGgggrrrrrr` |
| 3 | mixed(green+yellow) | 3 | `yyyggggrrrrrrrrrrrgygggrrrrrr` |
| 4 | green | 6 | `rrrGGgGrrrrrrrrrrrgrGgGrrrrrr` |
| 5 | mixed(green+yellow) | 3 | `rrryyyyrrrrrrrrrrryrygyrrrrrr` |
| 6 | green | 24 | `rrrrrrrrrrrrrGGGGgrrrGrrrrrrr` |
| 7 | yellow | 3 | `rrrrrrrrrrrrryyyyyrrryrrrrrrr` |

### J4 (program `0`, 20 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 25 | `GGgggrrrrrrrrrrGGGGg` |
| 1 | yellow | 3 | `yyyyyrrrrrrrrrryyyyy` |
| 2 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrr` |
| 3 | green | 27 | `rrrrrrrrrrGGGGgGrrrr` |
| 4 | mixed(green+yellow) | 3 | `rrrrrrrrrrGyyyyyrrrr` |
| 5 | green | 27 | `rrrrrGGGGgGrrrrrrrrr` |
| 6 | yellow | 3 | `rrrrryyyyyyrrrrrrrrr` |
| 7 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrr` |

### J5 (program `0`, 4 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 90 | `GGGG` |

### J6 (program `0`, 40 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 18 | `GGGGgggrrrrrrrrrrrrGGGGgggrrrrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyygggrrrrrrrrrrrryyyygggrrrrrrrrrrrrrr` |
| 2 | green | 6 | `rrrrGGGrrrrrrrrrrrrrrrrGGGrrrrrrrrrrrrrr` |
| 3 | yellow | 3 | `rrrryyyrrrrrrrrrrrrrrrryyyrrrrrrrrrrrrrr` |
| 4 | green | 18 | `rrrrrrrrrrrrrgGggggrrrrrrrrrrrrrGGGGgggg` |
| 5 | mixed(green+yellow) | 3 | `rrrrrrrrrrrrrgyggggrrrrrrrrrrrrryyyygggg` |
| 6 | green | 6 | `rrrrrrrrrrrrrgrGGgGrrrrrrrrrrrrrrrrrGGgG` |
| 7 | yellow | 3 | `rrrrrrrrrrrrryryyyyrrrrrrrrrrrrrrrrryyyy` |
| 8 | green | 18 | `rrrrrrrGGGgggrrrrrrrrrrrrrGGGgggrrrrrrrr` |
| 9 | mixed(green+yellow) | 3 | `rrrrrrryyygggrrrrrrrrrrrrryyygggrrrrrrrr` |
| 10 | green | 6 | `rrrrrrrrrrGGGrrrrrrrrrrrrrrrrGGGrrrrrrrr` |
| 11 | yellow | 3 | `rrrrrrrrrryyyrrrrrrrrrrrrrrrryyyrrrrrrrr` |

### J7 (program `0`, 42 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 18 | `gGGggggrrrrrrrrrrrrrrGGGGgggrrrrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `gyyggggrrrrrrrrrrrrrryyyygggrrrrrrrrrrrrrr` |
| 2 | green | 6 | `grrGGgGrrrrrrrrrrrrrrrrrrGgGrrrrrrrrrrrrrr` |
| 3 | yellow | 3 | `yrryyyyrrrrrrrrrrrrrrrrrryyyrrrrrrrrrrrrrr` |
| 4 | green | 18 | `rrrrrrrGGGGgggrrrrrrrrrrrrrrGGGGGgggrrrrrr` |
| 5 | mixed(green+yellow) | 3 | `rrrrrrryyyygggrrrrrrrrrrrrrryyyyygggrrrrrr` |
| 6 | green | 6 | `rrrrrrrrrrrGGGrrrrrrrrrrrrrrrrrrrGGGrrrrrr` |
| 7 | yellow | 3 | `rrrrrrrrrrryyyrrrrrrrrrrrrrrrrrrryyyrrrrrr` |
| 8 | green | 18 | `rrrrrrrrrrrrrrGGgggGgrrrrrrrrrrrrrrrgGgggg` |
| 9 | mixed(green+yellow) | 3 | `rrrrrrrrrrrrrryygggyyrrrrrrrrrrrrrrrgygggg` |
| 10 | green | 6 | `rrrrrrrrrrrrrrrrGGgrrrrrrrrrrrrrrrrrgrgGGG` |
| 11 | yellow | 3 | `rrrrrrrrrrrrrrrryyyrrrrrrrrrrrrrrrrryryyyy` |

### J8 (program `0`, 44 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 15 | `GGGGGGggrrrrrrrrGGGggggrrrrrrrrrrrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyyyyggrrrrrrrryyyggggrrrrrrrrrrrrrrrrrrrrr` |
| 2 | green | 6 | `rrrrrrGGrrrrrrrrrrrGGGGrrrrrrrrrrrrrrrrrrrrr` |
| 3 | yellow | 3 | `rrrrrryyrrrrrrrrrrryyyyrrrrrrrrrrrrrrrrrrrrr` |
| 4 | green | 15 | `rrrrrrrrGGGGGgggrrrrrrrrrrrrrrGGGGgggrrrrrrr` |
| 5 | mixed(green+yellow) | 3 | `rrrrrrrryyyyygggrrrrrrrrrrrrrryyyygggrrrrrrr` |
| 6 | green | 6 | `rrrrrrrrrrrrrGGGrrrrrrrrrrrrrrrrrrGGGrrrrrrr` |
| 7 | yellow | 3 | `rrrrrrrrrrrrryyyrrrrrrrrrrrrrrrrrryyyrrrrrrr` |
| 8 | green | 15 | `GrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrGGGGGGg` |
| 9 | yellow | 3 | `yrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrryyyyyyy` |
| 10 | green | 15 | `rrrrrrrrrrrrrrrrrrrrrrrGGGGGGgGrrrrrrrrrrrrr` |
| 11 | yellow | 3 | `rrrrrrrrrrrrrrrrrrrrrrryyyyyyyyrrrrrrrrrrrrr` |

### J9 (program `0`, 55 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 12 | `GGGGggggrrrrrrrrrrrrrrrrrrrrrrrGGGGGgggrrrrrrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyyggggrrrrrrrrrrrrrrrrrrrrrrryyyyygggrrrrrrrrrrrrrrrr` |
| 2 | green | 6 | `rrrrGGGGrrrrrrrrrrrrrrrrrrrrrrrrrrrrGGGrrrrrrrrrrrrrrrr` |
| 3 | yellow | 3 | `rrrryyyyrrrrrrrrrrrrrrrrrrrrrrrrrrrryyyrrrrrrrrrrrrrrrr` |
| 4 | green | 13 | `rrrrrrrrGGGggggrrrrrrrrrrrrrrrrrrrrrrrrgGGgggggrrrrrrrr` |
| 5 | mixed(green+yellow) | 3 | `rrrrrrrryyyggggrrrrrrrrrrrrrrrrrrrrrrrrgyygggggrrrrrrrr` |
| 6 | green | 6 | `rrrrrrrrrrrGgggrrrrrrrrrrrrrrrrrrrrrrrrgrrggGGGrrrrrrrr` |
| 7 | yellow | 3 | `rrrrrrrrrrryyyyrrrrrrrrrrrrrrrrrrrrrrrryrryyyyyrrrrrrrr` |
| 8 | green | 13 | `rrrrrrrrrrrrrrrrrrrrrrGGGGGggggrrrrrrrrrrrrrrrrgGGggggg` |
| 9 | mixed(green+yellow) | 3 | `rrrrrrrrrrrrrrrrrrrrrryyyyyggggrrrrrrrrrrrrrrrrgyyggggg` |
| 10 | green | 6 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrGGgGrrrrrrrrrrrrrrrrgrrGGGgG` |
| 11 | yellow | 3 | `rrrrrrrrrrrrrrrrrrrrrrrrrrryyyyrrrrrrrrrrrrrrrryrryyyyy` |
| 12 | green | 13 | `rrrrrrrrrrrrrrrGGGGGGgGrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 13 | yellow | 3 | `rrrrrrrrrrrrrrryyyyyyyyrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |

### J10 (program `0`, 29 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 20 | `GGGGggrrrrrrGGGgggrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyyggrrrrrryyygggrrrrrrrrrrr` |
| 2 | green | 6 | `rrrrGGrrrrrrrrrGGGrrrrrrrrrrr` |
| 3 | yellow | 3 | `rrrryyrrrrrrrrryyyrrrrrrrrrrr` |
| 4 | green | 21 | `rrrrrrGGGGggrrrrrrGGgggrrrrrr` |
| 5 | mixed(green+yellow) | 3 | `rrrrrryyyyggrrrrrryygggrrrrrr` |
| 6 | green | 6 | `rrrrrrrrrrGGrrrrrrrrGGGrrrrrr` |
| 7 | yellow | 3 | `rrrrrrrrrryyrrrrrrrryyyrrrrrr` |
| 8 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 9 | green | 21 | `GrrrrrrrrrrrrrrrrrrrrrrGGGGGg` |
| 10 | mixed(green+yellow) | 3 | `Grrrrrrrrrrrrrrrrrrrrrryyyyyy` |

### J11 (program `0`, 18 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 37 | `rrrrrGGggrrrrGGGgg` |
| 1 | mixed(green+yellow) | 3 | `rrrrryyggrrrryyygg` |
| 2 | green | 6 | `rrrrrrrGGrrrrrrrGG` |
| 3 | yellow | 3 | `rrrrrrryyrrrrrrryy` |
| 4 | all-red | 1 | `rrrrrrrrrrrrrrrrrr` |
| 5 | green | 36 | `gggggrrrrGGGgrrrrr` |
| 6 | yellow | 3 | `yyyyyrrrryyyyrrrrr` |
| 7 | all-red | 1 | `rrrrrrrrrrrrrrrrrr` |

### J12 (program `0`, 30 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 13 | `rrrrrrrrrrrrGGGGGgGGggggrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `rrrrrrrrrrrryyyyyyGGggggrrrrrr` |
| 2 | green | 6 | `rrrrrrrrrrrrrrrrrrGGGGGGrrrrrr` |
| 3 | yellow | 3 | `rrrrrrrrrrrrrrrrrryyyyyyrrrrrr` |
| 4 | all-red | 2 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 5 | green | 16 | `rrrrGrrrrrrrrrrrrrrrrrrrGGGGGg` |
| 6 | yellow | 3 | `rrrryrrrrrrrrrrrrrrrrrrryyyyyy` |
| 7 | all-red | 2 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 8 | green | 16 | `GGGGGgGrrrrrrrrrrrrrrrrrrrrrrr` |
| 9 | yellow | 3 | `yyyyyyyrrrrrrrrrrrrrrrrrrrrrrr` |
| 10 | all-red | 2 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 11 | green | 16 | `rrrrrrGGGGGgGrrrrrrrrrrrrrrrrr` |
| 12 | yellow | 3 | `rrrrrryyyyyyyrrrrrrrrrrrrrrrrr` |
| 13 | all-red | 2 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |

### J13 (program `0`, 40 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 18 | `rrrrrrGGGGgggrrrrrrrrrrrrrrGGGGgggrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `rrrrrryyyygggrrrrrrrrrrrrrryyyygggrrrrrr` |
| 2 | green | 6 | `rrrrrrrrrrGGGrrrrrrrrrrrrrrrrrrGGGrrrrrr` |
| 3 | yellow | 3 | `rrrrrrrrrryyyrrrrrrrrrrrrrrrrrryyyrrrrrr` |
| 4 | green | 18 | `rrrrrrrrrrrrrGGGGgggrrrrrrrrrrrrrrggGggg` |
| 5 | mixed(green+yellow) | 3 | `rrrrrrrrrrrrryyyygggrrrrrrrrrrrrrrggyggg` |
| 6 | green | 6 | `rrrrrrrrrrrrrrrrrGgGrrrrrrrrrrrrrrggrGGG` |
| 7 | yellow | 3 | `rrrrrrrrrrrrrrrrryyyrrrrrrrrrrrrrryyryyy` |
| 8 | green | 18 | `ggggggrrrrrrrrrrrrrrgGgGGggrrrrrrrrrrrrr` |
| 9 | mixed(green+yellow) | 3 | `ggggggrrrrrrrrrrrrrrgygyyggrrrrrrrrrrrrr` |
| 10 | green | 6 | `GGGgGgrrrrrrrrrrrrrrgrgrrggrrrrrrrrrrrrr` |
| 11 | yellow | 3 | `yyyyyyrrrrrrrrrrrrrryryrryyrrrrrrrrrrrrr` |

### J14 (program `0`, 12 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 42 | `rrrrGGGgGGgg` |
| 1 | mixed(green+yellow) | 3 | `rrrrGyyyyyyy` |
| 2 | green | 42 | `GGGgGrrrrrrr` |
| 3 | mixed(green+yellow) | 3 | `yyyyGrrrrrrr` |

### J15 (program `0`, 19 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 35 | `rrrrrGGGgggrrrrGggg` |
| 1 | yellow | 3 | `rrrrryyyyyyrrrryyyy` |
| 2 | all-red | 5 | `rrrrrrrrrrrrrrrrrrr` |
| 3 | green | 35 | `GGGggrrrrrrGGggrrrr` |
| 4 | mixed(green+yellow) | 3 | `yyyggrrrrrryyggrrrr` |
| 5 | green | 6 | `rrrGGrrrrrrrrGGrrrr` |
| 6 | yellow | 3 | `rrryyrrrrrrrryyrrrr` |

### J16 (program `0`, 31 controlled links)

| Phase | Classification | Duration (s) | State string |
|---|---|---|---|
| 0 | green | 22 | `GGGGggrrrrrrGGGGgggrrrrrrrrrrrr` |
| 1 | mixed(green+yellow) | 3 | `yyyyggrrrrrryyyygggrrrrrrrrrrrr` |
| 2 | green | 6 | `rrrrGGrrrrrrrrrrGGGrrrrrrrrrrrr` |
| 3 | yellow | 3 | `rrrryyrrrrrrrrrryyyrrrrrrrrrrrr` |
| 4 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 5 | green | 24 | `rrrrrrGGGGGgrrrrrrrggggggrrrrrr` |
| 6 | yellow | 3 | `rrrrrryyyyyyrrrrrrryyyyyyrrrrrr` |
| 7 | all-red | 1 | `rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr` |
| 8 | green | 24 | `GrrrrrrrrrrrrrrrrrrrrrrrrGGGGGg` |
| 9 | mixed(green+yellow) | 3 | `Grrrrrrrrrrrrrrrrrrrrrrrryyyyyy` |

