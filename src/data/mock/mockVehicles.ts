import { NormalVehicle, EmergencyVehicle } from '../../types';

export const MOCK_NORMAL_VEHICLES: NormalVehicle[] = [
  { id: 'CAR-101', type: 'car', fromJunctionId: 'J1', toJunctionId: 'J2', progressPercent: 35, speedKmh: 48, isBlue: true },
  { id: 'CAR-102', type: 'car', fromJunctionId: 'J4', toJunctionId: 'J5', progressPercent: 65, speedKmh: 42, isBlue: true },
  { id: 'CAR-103', type: 'car', fromJunctionId: 'J5', toJunctionId: 'J6', progressPercent: 20, speedKmh: 50, isBlue: true },
  { id: 'CAR-104', type: 'car', fromJunctionId: 'J6', toJunctionId: 'J7', progressPercent: 80, speedKmh: 44, isBlue: true },
  { id: 'CAR-105', type: 'car', fromJunctionId: 'J10', toJunctionId: 'J11', progressPercent: 50, speedKmh: 52, isBlue: true },
  { id: 'CAR-106', type: 'car', fromJunctionId: 'J11', toJunctionId: 'J12', progressPercent: 15, speedKmh: 46, isBlue: true },
  { id: 'BIKE-201', type: 'bike', fromJunctionId: 'J2', toJunctionId: 'J3', progressPercent: 40, speedKmh: 38, isBlue: true },
  { id: 'BIKE-202', type: 'bike', fromJunctionId: 'J5', toJunctionId: 'J10', progressPercent: 70, speedKmh: 35, isBlue: true },
  { id: 'BIKE-203', type: 'bike', fromJunctionId: 'J7', toJunctionId: 'J12', progressPercent: 25, speedKmh: 40, isBlue: true },
];

export const INITIAL_EMERGENCY_VEHICLE: EmergencyVehicle = {
  id: 'AMB-01',
  name: 'Ambulance Unit 01',
  type: 'ambulance',
  licensePlate: 'EMG-9941',
  priority: 'high',
  startJunctionId: 'J1',
  destinationName: 'Metro General Hospital',
  destinationJunctionId: 'J7',
  selectedHospitalId: 'H1',
  patientCondition: 'Cardiac Emergency',
  currentJunctionId: 'J1',
  progressPercent: 12,
  speedKmh: 54,
  headingDeg: 85,
  priorityScore: 92,
  priorityStatus: 'FAVOURED',
  greenCorridorActive: true,
  accumulatedDelayMin: 0,
  currentRoadId: 'R4',
  route: {
    id: 'opt-rec',
    name: 'Recommended Green Corridor',
    isRecommended: true,
    pathJunctionIds: ['J1', 'J5', 'J6', 'J7'],
    totalDistanceKm: 4.0,
    etaMinutes: 6.5,
    trafficSummary: 'Clear',
    greenCorridorSupported: true,
    reasons: [
      'Lowest current estimated travel time (6.5 min vs 9.2 min)',
      'Avoids active road construction on Tech Center Bypass',
      'Avoids severe congestion on Pine Expressway approaching J3',
      'Full Dynamic Green Corridor preemption confirmed across J1, J5, J6, J7',
      'Direct specialty match for Cardiac Emergency at Metro General Hospital'
    ],
    color: '#10B981',
  },
  alternateRoutes: [
    {
      id: 'opt-alt-1',
      name: 'Alternate via North Ring',
      isRecommended: false,
      pathJunctionIds: ['J1', 'J2', 'J3', 'J7'],
      totalDistanceKm: 4.1,
      etaMinutes: 9.2,
      trafficSummary: 'Heavy',
      greenCorridorSupported: true,
      reasons: [
        'Slightly shorter physical distance but +2.7 min delay due to Pine Expressway congestion',
        'Wet pavement on R2 with rain advisory'
      ],
      color: '#3B82F6',
    },
    {
      id: 'opt-alt-2',
      name: 'Alternate via South Parkway',
      isRecommended: false,
      pathJunctionIds: ['J1', 'J4', 'J5', 'J6', 'J7'],
      totalDistanceKm: 4.9,
      etaMinutes: 8.0,
      trafficSummary: 'Moderate',
      greenCorridorSupported: false,
      reasons: [
        'Bypasses primary urban arterial',
        'Green corridor preemption limited on Civic West Way'
      ],
      color: '#F59E0B',
    }
  ]
};
