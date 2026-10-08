import {
  EmergencyVehicle,
  RouteOption,
  VehicleType,
} from '../types';

import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';
import { MOCK_ROADS } from '../data/mock/mockRoads';
import { MOCK_WEATHER } from '../data/mock/mockConditions';

// ============================================================
// TYPES
// ============================================================

export type PriorityLevel = 'high' | 'medium' | 'low';

interface PriorityFactor {
  value: number;
  weight: number;
  score: number;
  detail: string;
}

export interface DynamicPriorityBreakdown {
  vehicleId: string;
  vehicleType: VehicleType;
  totalScore: number;
  factors: Record<string, PriorityFactor>;
  tieBreakerApplied: boolean;
  tieBreakerReason?: string;
  reasons: string[];
}

export interface PriorityWeights {
  urgencyWeight: number;
  etaWeight: number;
  junctionWeight: number;
  trafficWeight: number;
  conflictWeight: number;
  delayWeight: number;
}

// ============================================================
// LOCAL TYPES
// These prevent errors if your main Junction/Road types
// do not contain these optional properties.
// ============================================================

interface JunctionWithConnections {
  id: string;
  connectedJunctions?: string[];
}

interface RoadWithDistance {
  fromJunction?: string;
  toJunction?: string;
  fromJunctionId?: string;
  toJunctionId?: string;
  distanceKm?: number;
  distanceMeters?: number;
}

// ============================================================
// DEFAULT PRIORITY WEIGHTS
// ============================================================

const DEFAULT_WEIGHTS: PriorityWeights = {
  urgencyWeight: 0.30,
  etaWeight: 0.20,
  junctionWeight: 0.20,
  trafficWeight: 0.10,
  conflictWeight: 0.10,
  delayWeight: 0.10,
};

// ============================================================
// ROUTING SERVICE
// ============================================================

export const routingService = {

  // ==========================================================
  // CALCULATE BEST ROUTE
  // ==========================================================

  calculateBestRoute(
    startJunctionId: string,
    destinationJunctionId: string,
    vehicleType: VehicleType,
    conditionOrDestination: string,
    priority: PriorityLevel
  ): {
    recommended: RouteOption;
    alternates: RouteOption[];
  } {

    const startJunc = MOCK_JUNCTIONS.find(
      (j) => j.id === startJunctionId
    );

    const destJunc = MOCK_JUNCTIONS.find(
      (j) => j.id === destinationJunctionId
    );

    const startId = startJunc?.id ?? startJunctionId;
    const destId = destJunc?.id ?? destinationJunctionId;

    let primaryPath: string[] = [];
    let altPath1: string[] = [];
    let altPath2: string[] = [];

    // ========================================================
    // KNOWN DEMO ROUTES
    // ========================================================

    if (startId === 'J1' && (destId === 'J7' || destId === 'HOSP3' || destId === 'H1')) {
      primaryPath = ['J1', 'J2', 'J7'];
      altPath1 = ['J1', 'J6', 'J7'];
      altPath2 = ['J1', 'J2', 'J3', 'J8', 'J7'];
    } else if (startId === 'J2' && destId === 'J8') {
      primaryPath = ['J2', 'J3', 'J8'];
      altPath1 = ['J2', 'J7', 'J8'];
      altPath2 = ['J2', 'J1', 'J6', 'J8'];
    } else if (startId === 'J4' && destId === 'J12') {
      primaryPath = ['J4', 'J9', 'J7', 'J12'];
      altPath1 = ['J4', 'J3', 'J2', 'J12'];
      altPath2 = ['J4', 'J9', 'J14', 'J13', 'J12'];
    } else {

      // ======================================================
      // GENERAL GRAPH SEARCH
      // ======================================================

      primaryPath = this.findPath(
        startId,
        destId,
        false
      );

      altPath1 = this.findPath(
        startId,
        destId,
        true
      );

      altPath2 = this.findPath(
        startId,
        destId,
        false
      );
    }

    // ========================================================
    // SAFETY CHECK
    // ========================================================

    if (primaryPath.length < 2) {
      primaryPath = [
        startId,
        destId,
      ];
    }

    if (altPath1.length < 2) {
      altPath1 = [
        startId,
        destId,
      ];
    }

    if (altPath2.length < 2) {
      altPath2 = [
        startId,
        destId,
      ];
    }

    // ========================================================
    // ROUTE STATISTICS
    // ========================================================

    const recStats = this.calculateRouteStats(
      primaryPath,
      true
    );

    const alt1Stats = this.calculateRouteStats(
      altPath1,
      false
    );

    const alt2Stats = this.calculateRouteStats(
      altPath2,
      false
    );

    // ========================================================
    // ROUTE REASONS
    // ========================================================

    const recReasons = this.generateRouteReasons(
      primaryPath,
      recStats.distanceKm,
      recStats.etaMinutes,
      vehicleType,
      conditionOrDestination,
      priority
    );

    // ========================================================
    // RECOMMENDED ROUTE
    // ========================================================

    const recommended: RouteOption = {
      id: `rt-rec-${Date.now()}`,
      name: 'Recommended Green Corridor',
      isRecommended: true,
      pathJunctionIds: primaryPath,
      totalDistanceKm: recStats.distanceKm,
      etaMinutes: recStats.etaMinutes,
      trafficSummary: recStats.trafficSummary,
      greenCorridorSupported: true,
      reasons: recReasons,
      color: '#10B981',
    };

    // ========================================================
    // ALTERNATE ROUTE 1
    // ========================================================

    const alternate1: RouteOption = {
      id: `rt-alt1-${Date.now()}`,
      name: 'Alternate via Expressway',
      isRecommended: false,
      pathJunctionIds: altPath1,
      totalDistanceKm: alt1Stats.distanceKm,
      etaMinutes: alt1Stats.etaMinutes,
      trafficSummary: alt1Stats.trafficSummary,
      greenCorridorSupported: true,

      reasons: [
        'Higher speed limits along arterial segments',

        alt1Stats.trafficSummary === 'Heavy'
          ? 'Slower average speed due to peak lane traffic'
          : 'Alternative bypass route',
      ],

      color: '#3B82F6',
    };

    // ========================================================
    // ALTERNATE ROUTE 2
    // ========================================================

    const alternate2: RouteOption = {
      id: `rt-alt2-${Date.now()}`,
      name: 'Alternate via Outer Ring',
      isRecommended: false,
      pathJunctionIds: altPath2,
      totalDistanceKm: alt2Stats.distanceKm,
      etaMinutes: alt2Stats.etaMinutes,
      trafficSummary: alt2Stats.trafficSummary,
      greenCorridorSupported: false,

      reasons: [
        'Wider turning radius suitable for heavy emergency units',
        'Partial civilian signal coordination on secondary junctions',
      ],

      color: '#F59E0B',
    };

    return {
      recommended,
      alternates: [
        alternate1,
        alternate2,
      ],
    };
  },

  // ==========================================================
  // FIND PATH
  // ==========================================================

  findPath(
    startId: string,
    endId: string,
    alternate = false
  ): string[] {

    if (startId === endId) {
      return [startId];
    }

    const visited = new Set<string>();

    const queue: {
      current: string;
      path: string[];
    }[] = [
      {
        current: startId,
        path: [startId],
      },
    ];

    while (queue.length > 0) {

      const item = alternate
        ? queue.pop()
        : queue.shift();

      if (!item) {
        break;
      }

      const current = item.current;
      const path = item.path;

      if (current === endId) {
        return path;
      }

      if (visited.has(current)) {
        continue;
      }

      visited.add(current);

      // ======================================================
      // FIX FOR connectedJunctions TYPE ERROR
      // ======================================================

      const foundJunction = MOCK_JUNCTIONS.find(
        (j) => j.id === current
      );

      if (!foundJunction) {
        continue;
      }

      const junc =
        foundJunction as unknown as JunctionWithConnections;

      const connections: string[] =
        junc.connectedJunctions ?? [];

      const neighbors: string[] = alternate
        ? [...connections].reverse()
        : [...connections];

      for (const next of neighbors) {

        if (!visited.has(next)) {

          queue.push({
            current: next,
            path: [
              ...path,
              next,
            ],
          });

        }
      }
    }

    // No path found
    return [
      startId,
      endId,
    ];
  },

  // ==========================================================
  // CALCULATE ROUTE STATISTICS
  // ==========================================================

  calculateRouteStats(
    path: string[],
    isRecommended: boolean
  ): {
    distanceKm: number;
    etaMinutes: number;
    trafficSummary: 'Clear' | 'Moderate' | 'Heavy';
  } {

    let distance = 0;

    // ========================================================
    // CALCULATE ROAD DISTANCE
    // ========================================================

    for (
      let i = 0;
      i < path.length - 1;
      i++
    ) {

      const from = path[i];
      const to = path[i + 1];

      const foundRoad = MOCK_ROADS.find(
        (r) => {

          const road =
            r as unknown as RoadWithDistance;

          const normalDirection =
            road.fromJunction === from &&
            road.toJunction === to;

          const reverseDirection =
            road.fromJunction === to &&
            road.toJunction === from;

          const normalIdDirection =
            road.fromJunctionId === from &&
            road.toJunctionId === to;

          const reverseIdDirection =
            road.fromJunctionId === to &&
            road.toJunctionId === from;

          return (
            normalDirection ||
            reverseDirection ||
            normalIdDirection ||
            reverseIdDirection
          );
        }
      );

      if (foundRoad) {

        const road =
          foundRoad as unknown as RoadWithDistance;

        let roadDistance: number | undefined;

        if (
          road.distanceKm !== undefined
        ) {

          roadDistance =
            road.distanceKm;

        } else if (
          road.distanceMeters !== undefined
        ) {

          roadDistance =
            road.distanceMeters / 1000;

        }

        if (
          roadDistance !== undefined &&
          Number.isFinite(roadDistance) &&
          roadDistance > 0
        ) {

          distance += roadDistance;

        } else {

          distance += 1.2;
        }

      } else {

        // Safe fallback
        distance += 1.2;
      }
    }

    // ========================================================
    // VALIDATE DISTANCE
    // ========================================================

    if (
      !Number.isFinite(distance) ||
      distance <= 0
    ) {

      distance = 3.5;
    }

    distance = Number(
      distance.toFixed(1)
    );

    // ========================================================
    // ETA
    // ========================================================

    let baseEta = Number(
      (
        distance * 1.4
      ).toFixed(1)
    );

    if (!isRecommended) {

      baseEta = Number(
        (
          baseEta * 1.35 + 1.2
        ).toFixed(1)
      );
    }

    // ========================================================
    // TRAFFIC
    // ========================================================

    let trafficSummary:
      | 'Clear'
      | 'Moderate'
      | 'Heavy';

    if (isRecommended) {

      trafficSummary = 'Clear';

    } else if (baseEta > 8) {

      trafficSummary = 'Heavy';

    } else {

      trafficSummary = 'Moderate';
    }

    // ========================================================
    // RETURN
    // ========================================================

    return {
      distanceKm: distance,
      etaMinutes: Math.max(
        2.5,
        baseEta
      ),
      trafficSummary,
    };
  },

  // ==========================================================
  // GENERATE ROUTE REASONS
  // ==========================================================

  generateRouteReasons(
    path: string[],
    distanceKm: number,
    etaMinutes: number,
    vehicleType: VehicleType,
    conditionOrDestination: string,
    priority: PriorityLevel
  ): string[] {

    const reasons: string[] = [];

    // ========================================================
    // TRAVEL TIME
    // ========================================================

    reasons.push(
      `Lowest current estimated travel time (${etaMinutes} min) for ${distanceKm} km transit.`
    );

    // ========================================================
    // TRAFFIC
    // ========================================================

    const avoidsHeavy =
      !path.includes('J2') ||
      !path.includes('J3');

    if (avoidsHeavy) {

      reasons.push(
        'Avoids severe peak-hour congestion on Pine Expressway approaching Junction 3.'
      );

    } else {

      reasons.push(
        'Green Corridor preemption active to flush traffic ahead of unit.'
      );
    }

    // ========================================================
    // ROAD CONSTRUCTION
    // ========================================================

    const hasConstruction =
      path.includes('J2') &&
      path.includes('J6');

    if (!hasConstruction) {

      reasons.push(
        'Avoids active road construction and lane closures on Tech Center Bypass.'
      );
    }

    // ========================================================
    // WEATHER
    // ========================================================

    const weatherCondition =
      String(
        MOCK_WEATHER?.condition ?? ''
      );

    if (
      weatherCondition
        .toLowerCase()
        .includes('rain')
    ) {

      reasons.push(
        `Favorable road gradient avoiding waterlogged segments during ${weatherCondition}.`
      );
    }

    // ========================================================
    // GREEN CORRIDOR
    // ========================================================

    reasons.push(
      `Full dynamic green corridor signal preemption enabled across ${path.length} synchronized junctions.`
    );

    // ========================================================
    // VEHICLE TYPE
    // ========================================================

    if (
      vehicleType === 'ambulance'
    ) {

      reasons.push(
        `Direct facility match verified for ${conditionOrDestination || 'emergency care'} with priority ICU access.`
      );

    } else if (
      vehicleType === 'fireEngine'
    ) {

      reasons.push(
        'Clear arterial turning radiuses optimized for heavy fire and rescue apparatus.'
      );

    } else {

      reasons.push(
        'High-speed tactical transit corridor prioritized with minimum civilian interference.'
      );
    }

    // ========================================================
    // PRIORITY
    // ========================================================

    if (
      priority === 'high'
    ) {

      reasons.push(
        'Classified as HIGH urgency response — pre-clearing oncoming civilian signals.'
      );
    }

    return reasons;
  },

  // ==========================================================
  // DYNAMIC PRIORITY SCORE
  // ==========================================================

  calculateDynamicPriorityScore(
    vehicle: EmergencyVehicle,
    contestedJunctionId?: string,
    allVehicles: EmergencyVehicle[] = []
  ): DynamicPriorityBreakdown {

    const weights = DEFAULT_WEIGHTS;

    // ========================================================
    // 1. EMERGENCY URGENCY
    // ========================================================

    let urgencyVal = 30;

    let urgencyDetail =
      'Low non-critical urgency';

    if (
      vehicle.priority === 'high'
    ) {

      urgencyVal = 100;

      urgencyDetail =
        'High critical life-safety emergency';

    } else if (
      vehicle.priority === 'medium'
    ) {

      urgencyVal = 60;

      urgencyDetail =
        'Medium urgent response';
    }

    // ========================================================
    // 2. ETA URGENCY
    // ========================================================

    const etaMin =
      Number(
        vehicle.route?.etaMinutes
      ) || 7;

    const etaUrgencyVal =
      Math.min(
        100,
        Math.max(
          10,
          Math.round(
            100 - etaMin * 6
          )
        )
      );

    const etaDetail =
      `Current ETA: ${etaMin} min (time criticality: ${etaUrgencyVal}/100)`;

    // ========================================================
    // 3. JUNCTION PROXIMITY
    // ========================================================

    const progress =
      Number(
        vehicle.progressPercent
      ) || 0;

    let proxVal = 60;

    let proxDetail =
      'Standard transit distance to intersection';

    if (progress >= 80) {

      proxVal = 95;

      proxDetail =
        'Immediate intersection proximity (< 150m) - priority signal lock';

    } else if (progress >= 50) {

      proxVal = 70;

      proxDetail =
        'Moderate proximity (~400m from intersection)';

    } else {

      proxVal = 40;

      proxDetail =
        'Approaching transit (~750m distance)';
    }

    // ========================================================
    // 4. TRAFFIC
    // ========================================================

    let trafficVal = 50;

    let trafficDetail =
      'Moderate traffic density';

    const trafficSummary =
      vehicle.route?.trafficSummary;

    if (
      trafficSummary === 'Heavy'
    ) {

      trafficVal = 90;

      trafficDetail =
        'Severe congestion requiring aggressive corridor preemption';

    } else if (
      trafficSummary === 'Clear'
    ) {

      trafficVal = 40;

      trafficDetail =
        'Clear lane flow';
    }

    // ========================================================
    // 5. ROUTE CONFLICT
    // ========================================================

    const hasConflict =
      allVehicles.some(
        (otherVehicle) => {

          if (
            otherVehicle.id ===
            vehicle.id
          ) {

            return false;
          }

          const contestedMatch =
            Boolean(
              contestedJunctionId &&
              otherVehicle.route?.pathJunctionIds?.includes(
                contestedJunctionId
              )
            );

          const sharedRoute =
            Boolean(
              vehicle.route?.pathJunctionIds?.some(
                (junctionId) =>
                  otherVehicle.route?.pathJunctionIds?.includes(
                    junctionId
                  )
              )
            );

          return (
            contestedMatch ||
            sharedRoute
          );
        }
      );

    const conflictVal =
      hasConflict
        ? 85
        : 30;

    const conflictDetail =
      hasConflict
        ? 'Contested junction with active emergency unit'
        : 'Uncontested dedicated corridor';

    // ========================================================
    // 6. ACCUMULATED DELAY
    // ========================================================

    const delayMin =
      Number(
        vehicle.accumulatedDelayMin
      ) || 0;

    const delayVal =
      Math.min(
        100,
        Math.max(
          10,
          delayMin * 25 + 20
        )
      );

    const delayDetail =
      delayMin > 0
        ? `+${delayMin} min previous accumulated delay`
        : 'On-schedule transit (0 min delay)';

    // ========================================================
    // WEIGHTED SCORES
    // ========================================================

    const urgencyScore =
      Number(
        (
          weights.urgencyWeight *
          urgencyVal
        ).toFixed(2)
      );

    const etaScore =
      Number(
        (
          weights.etaWeight *
          etaUrgencyVal
        ).toFixed(2)
      );

    const proxScore =
      Number(
        (
          weights.junctionWeight *
          proxVal
        ).toFixed(2)
      );

    const trafficScore =
      Number(
        (
          weights.trafficWeight *
          trafficVal
        ).toFixed(2)
      );

    const conflictScore =
      Number(
        (
          weights.conflictWeight *
          conflictVal
        ).toFixed(2)
      );

    const delayScore =
      Number(
        (
          weights.delayWeight *
          delayVal
        ).toFixed(2)
      );

    // ========================================================
    // TOTAL SCORE
    // ========================================================

    const totalScore =
      Math.round(
        urgencyScore +
        etaScore +
        proxScore +
        trafficScore +
        conflictScore +
        delayScore
      );

    // ========================================================
    // REASONS
    // ========================================================

    const reasons: string[] = [];

    if (
      urgencyVal >= 90
    ) {

      reasons.push(
        'High emergency urgency level (life-critical protocol).'
      );
    }

    if (
      proxVal >= 80
    ) {

      reasons.push(
        'Closest proximity to contested junction lock point.'
      );
    }

    if (
      trafficVal >= 80
    ) {

      reasons.push(
        'Heavy opposing congestion requiring preemption clearance.'
      );
    }

    if (
      delayMin > 0
    ) {

      reasons.push(
        `${delayMin} min accumulated delay factored into priority boost.`
      );
    }

    if (
      hasConflict
    ) {

      reasons.push(
        'Contested junction preemption arbitration evaluated.'
      );
    }

    // ========================================================
    // RETURN BREAKDOWN
    // ========================================================

    return {

      vehicleId:
        vehicle.id,

      vehicleType:
        vehicle.type,

      totalScore,

      factors: {

        emergencyUrgency: {
          value: urgencyVal,
          weight: weights.urgencyWeight,
          score: urgencyScore,
          detail: urgencyDetail,
        },

        etaUrgency: {
          value: etaUrgencyVal,
          weight: weights.etaWeight,
          score: etaScore,
          detail: etaDetail,
        },

        junctionProximity: {
          value: proxVal,
          weight: weights.junctionWeight,
          score: proxScore,
          detail: proxDetail,
        },

        trafficCondition: {
          value: trafficVal,
          weight: weights.trafficWeight,
          score: trafficScore,
          detail: trafficDetail,
        },

        routeConflict: {
          value: conflictVal,
          weight: weights.conflictWeight,
          score: conflictScore,
          detail: conflictDetail,
        },

        accumulatedDelay: {
          value: delayVal,
          weight: weights.delayWeight,
          score: delayScore,
          detail: delayDetail,
        },
      },

      tieBreakerApplied: false,

      reasons,
    };
  },

  // ==========================================================
  // RESOLVE VEHICLE CONFLICT
  // ==========================================================

  resolveVehicleConflict(
    vehicles: EmergencyVehicle[],
    contestedJunctionId = 'J3'
  ): {
    favouredVehicleId: string;
    breakdowns: Record<string, DynamicPriorityBreakdown>;
    tieBreakerUsed: boolean;
    explanation: string[];
  } {

    // ========================================================
    // NO VEHICLES
    // ========================================================

    if (
      vehicles.length === 0
    ) {

      return {
        favouredVehicleId: '',
        breakdowns: {},
        tieBreakerUsed: false,
        explanation: [],
      };
    }

    // ========================================================
    // CALCULATE BREAKDOWNS
    // ========================================================

    const breakdowns:
      Record<
        string,
        DynamicPriorityBreakdown
      > = {};

    for (
      const vehicle of vehicles
    ) {

      breakdowns[vehicle.id] =
        this.calculateDynamicPriorityScore(
          vehicle,
          contestedJunctionId,
          vehicles
        );
    }

    // ========================================================
    // SORT VEHICLES
    // ========================================================

    const sorted =
      [...vehicles].sort(
        (a, b) => {

          const scoreA =
            breakdowns[a.id]
              .totalScore;

          const scoreB =
            breakdowns[b.id]
              .totalScore;

          // Highest score wins
          if (
            scoreA !== scoreB
          ) {

            return scoreB - scoreA;
          }

          // ==================================================
          // TIE BREAKER
          // Fire Engine > Ambulance > Police
          // ==================================================

          const precedence:
            Record<VehicleType, number> = {

              fireEngine: 3,

              ambulance: 2,

              police: 1,
            };

          return (
            precedence[b.type] -
            precedence[a.type]
          );
        }
      );

    // ========================================================
    // WINNER
    // ========================================================

    const winner =
      sorted[0];

    const runnerUp =
      sorted[1];

    let tieBreakerUsed =
      false;

    const explanation:
      string[] = [];

    // ========================================================
    // TIE BREAKER DETECTION
    // ========================================================

    if (
      runnerUp &&
      breakdowns[winner.id].totalScore ===
        breakdowns[runnerUp.id].totalScore
    ) {

      tieBreakerUsed = true;

      breakdowns[winner.id]
        .tieBreakerApplied = true;

      breakdowns[winner.id]
        .tieBreakerReason =
        `Equal score (${breakdowns[winner.id].totalScore}) resolved by service precedence (${winner.type} over ${runnerUp.type}).`;

      explanation.push(
        'Dynamic priority scores were equal.'
      );

      explanation.push(
        `${winner.name} selected by standard emergency service precedence tie-breaker.`
      );

    } else {

      explanation.push(
        `Highest Dynamic Priority Score (${breakdowns[winner.id].totalScore} vs ${
          runnerUp
            ? breakdowns[runnerUp.id].totalScore
            : 'N/A'
        }).`
      );

      explanation.push(
        ...breakdowns[winner.id].reasons
      );
    }

    // ========================================================
    // RETURN
    // ========================================================

    return {

      favouredVehicleId:
        winner.id,

      breakdowns,

      tieBreakerUsed,

      explanation,
    };
  },
};