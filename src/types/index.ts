// ============================================================
// RESQROUTE - SHARED TYPES
// ============================================================

export type VehicleType =
  | 'ambulance'
  | 'fireEngine'
  | 'police';

export type EmergencyPriority =
  | 'high'
  | 'medium'
  | 'low';

export type GPSAccuracyStatus =
  | 'STRONG'
  | 'MEDIUM'
  | 'WEAK'
  | 'UNAVAILABLE';

export interface GPSState {
  lat: number | null;
  lng: number | null;
  accuracyMeters: number | null;
  headingDeg: number | null;
  speedKmh: number | null;
  status: GPSAccuracyStatus;
  isRealGps: boolean;
  errorMessage?: string;
}

export type PriorityLevel = EmergencyPriority;

export interface User {
  id?: string;
  vehicleId: string;
  licenseNumber: string;
  vehicleType: VehicleType;
  officerName?: string;
  rememberDevice?: boolean;
  name?: string;
  email?: string;
  avatar?: string;
}

export interface PatientCondition {
  id: string;
  name: string;
  icon?: string;
  isSpecialized?: boolean;
  requiredSpecialty?: string;
  severity?: PriorityLevel;
  recommendedHospitalType?: string;
  specialtyRequired?: string;
  description?: string;
}

export interface ControlledJunctionState {
  junctionId: string;
  id?: string;
  signalState: 'green' | 'red' | 'yellow';
  preemption: 'STANDBY' | 'REQUESTED' | 'ACTIVE' | 'COMPLETED';
  recoveryStatus: 'PENDING' | 'ACTIVE' | 'RECOVERED';
  isPreempted?: boolean;
  state?: 'green' | 'yellow' | 'red';
}

export interface GreenCorridorState {
  corridorId?: string;
  routeId?: string;
  vehicleId?: string;
  isActive: boolean;
  junctions: ControlledJunctionState[];
}

// ============================================================
// JUNCTION
// ============================================================

export interface Junction {
  id: string;
  name?: string;
  latitude: number;
  longitude: number;

  lat?: number;
  lng?: number;

  x?: number;
  y?: number;

  signalId?: string;
  signalState?: string;
  preemptionStatus?: string;
  connectedJunctions?: string[];
  isEmergencyCorridor?: boolean;
}

// ============================================================
// ROAD
// ============================================================

export interface Road {
  id: string;

  name?: string;

  fromJunctionId?: string;
  toJunctionId?: string;

  fromJunction?: string;
  toJunction?: string;

  from?: string;
  to?: string;

  lengthKm?: number;
  distanceKm?: number;
  distanceMeters?: number;

  lanes?: number;
  speedLimitKmh?: number;
  currentSpeedKmh?: number;
  averageSpeedKmh?: number;

  trafficLevel?: string;
  trafficDensity?: number;
  congestion?: number;

  travelTimeMinutes?: number;
  condition?: string;
  conditionDetails?: string;

  isBlocked?: boolean;
  isUnderConstruction?: boolean;

  geometry?: Array<{
    latitude: number;
    longitude: number;
    x?: number;
    y?: number;
  }>;
}

// ============================================================
// HOSPITAL
// ============================================================

export interface Hospital {
  id: string;
  name: string;

  latitude: number;
  longitude: number;

  lat?: number;
  lng?: number;

  x?: number;
  y?: number;

  junctionId?: string;
  address?: string;

  specialties?: string[];
  capacityLevel?: string;
  emergencyRoomsFree?: number;
  phone?: string;

  emergencyCapacity?: number;
  availableBeds?: number;

  traumaCenter?: boolean;
  isEmergencyHospital?: boolean;
}

// ============================================================
// ROUTE
// ============================================================

export interface RouteOption {
  id: string;
  name: string;

  isRecommended: boolean;

  pathJunctionIds: string[];

  totalDistanceKm: number;
  etaMinutes: number;

  trafficSummary: string;

  greenCorridorSupported: boolean;

  reasons: string[];

  color?: string;

  roads?: Road[];

  distanceMeters?: number;
  estimatedTimeMinutes?: number;
  score?: number;
}

// ============================================================
// TURN MANEUVER
// ============================================================

export type TurnManeuver =
  | 'straight'
  | 'left'
  | 'right'
  | 'slight-left'
  | 'slight-right'
  | 'u-turn'
  | 'turn_left'
  | 'turn_right'
  | 'slight_left'
  | 'slight_right'
  | 'arrive';

// ============================================================
// TURN INSTRUCTION
// ============================================================

export interface TurnInstruction {
  id: string;

  instruction: string;

  maneuver: TurnManeuver;

  distanceMeters: number;

  junctionId: string;

  roadName: string;

  fromJunction?: string;
  toJunction?: string;

  distanceKm?: number;

  exitNumber?: number;
}

// ============================================================
// LIVE GPS
// ============================================================

export interface LiveGPS {
  lat: number;
  lng: number;

  accuracyMeters: number;

  isReal: boolean;
}

// ============================================================
// EMERGENCY VEHICLE
// ============================================================

export interface EmergencyVehicle {
  id: string;

  name: string;

  type: VehicleType;

  licensePlate: string;

  priority: EmergencyPriority;

  startJunctionId: string;

  destinationName: string;

  destinationJunctionId: string;

  selectedHospitalId?: string;

  patientCondition?: string;

  currentJunctionId: string;

  progressPercent: number;

  speedKmh: number;

  headingDeg: number;

  priorityScore: number;

  priorityStatus: string;

  greenCorridorActive: boolean;

  accumulatedDelayMin: number;

  currentRoadId?: string;

  route: RouteOption;

  alternateRoutes: RouteOption[];

  liveGps?: LiveGPS;

  latitude?: number;
  longitude?: number;

  remainingDistanceKm?: number;
  remainingEtaMinutes?: number;
}

// ============================================================
// NORMAL VEHICLE
// ============================================================

export interface NormalVehicle {
  id: string;

  type?: string;
  name?: string;

  roadId?: string;
  currentRoadId?: string;
  fromJunctionId?: string;
  toJunctionId?: string;

  progressPercent: number;

  speedKmh?: number;

  headingDeg?: number;

  currentJunctionId?: string;

  latitude?: number;
  longitude?: number;

  color?: string;
  isBlue?: boolean;
}

// ============================================================
// SCENARIO
// ============================================================

export interface Scenario {
  id: string;

  title: string;
  name?: string;

  description?: string;

  vehicles: EmergencyVehicle[];

  normalVehicles?: NormalVehicle[];

  activeVehicleId?: string;

  trafficLevel?: string;

  weather?: string;

  hasConflict?: boolean;

  highlightJunctionId?: string;
}

// ============================================================
// TRAFFIC DATA
// ============================================================

export interface TrafficData {
  id?: string;

  vehicleId?: string;

  roadId?: string;

  latitude?: number;
  longitude?: number;

  speedKmh?: number;

  density?: number;

  congestion?: number;

  trafficLevel?: string;
}

// ============================================================
// WEATHER
// ============================================================

export interface WeatherData {
  condition: string;

  temperatureC?: number;

  visibilityKm?: number;

  rainfallMm?: number;

  windSpeedKmh?: number;

  rainIntensity?: string;

  affectedRoadIds?: string[];

  advisory?: string;

  description?: string;
}

// ============================================================
// C2 - DISASTER MODE
// ============================================================

export type DisasterStatus = 'ACTIVE' | 'INACTIVE';

export interface DisasterMode {
  status: DisasterStatus;
  disasterType?: string;
  description?: string;
  activatedAt?: string;
  activatedBy?: string;
}

// ============================================================
// C2 - AUTHORIZED VEHICLE REGISTRY
// ============================================================

export interface AuthorizedVehicle {
  id: string;
  vehicleId: string;
  vehicleType: VehicleType;
  licensePlate: string;
  authority: 'police' | 'hospital' | 'disaster_authority';
  authorized: boolean;
  registeredAt: string;
  registeredBy?: string;
}

// ============================================================
// C2 - EVENT TIMELINE
// ============================================================

export type C2EventType =
  | 'DISASTER_ACTIVATED'
  | 'DISASTER_DEACTIVATED'
  | 'VEHICLE_REGISTERED'
  | 'VEHICLE_REVOKED'
  | 'EMERGENCY_STARTED'
  | 'EMERGENCY_COMPLETED';

export interface C2Event {
  id: string;
  type: C2EventType;
  title: string;
  description: string;
  timestamp: string;
  vehicleId?: string;
}

// ============================================================
// C2 - PERFORMANCE DASHBOARD
// ============================================================

export interface C2Performance {
  totalEvents: number;
  activeEmergencies: number;
  completedEmergencies: number;
  authorizedVehicles: number;
  revokedVehicles: number;
  averageEtaMinutes: number;
}