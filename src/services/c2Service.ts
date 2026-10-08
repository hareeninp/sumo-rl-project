import {
  AuthorizedVehicle,
  C2Event,
  C2Performance,
  DisasterMode,
  EmergencyVehicle,
  VehicleType,
} from '../types';

const DISASTER_KEY = 'resqroute_c2_disaster';
const VEHICLES_KEY = 'resqroute_c2_authorized_vehicles';
const EVENTS_KEY = 'resqroute_c2_events';

const readStorage = <T>(key: string, fallback: T): T => {
  try {
    const value = localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
};

const writeStorage = <T>(key: string, value: T) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore storage errors.
  }
};

const createEvent = (
  type: C2Event['type'],
  title: string,
  description: string,
  vehicleId?: string
): C2Event => {
  const event: C2Event = {
    id: `c2-event-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 7)}`,
    type,
    title,
    description,
    timestamp: new Date().toISOString(),
    vehicleId,
  };

  const events = readStorage<C2Event[]>(EVENTS_KEY, []);

  writeStorage(EVENTS_KEY, [event, ...events].slice(0, 100));

  return event;
};

export const c2Service = {
  // ==========================================================
  // DISASTER MODE
  // ==========================================================

  getDisasterMode(): DisasterMode {
    return readStorage<DisasterMode>(DISASTER_KEY, {
      status: 'INACTIVE',
    });
  },

  activateDisasterMode(
    disasterType: string,
    description: string,
    activatedBy: string
  ): DisasterMode {
    const disaster: DisasterMode = {
      status: 'ACTIVE',
      disasterType,
      description,
      activatedAt: new Date().toISOString(),
      activatedBy,
    };

    writeStorage(DISASTER_KEY, disaster);

    createEvent(
      'DISASTER_ACTIVATED',
      'Disaster mode activated',
      `${disasterType}: ${description}`
    );

    return disaster;
  },

  deactivateDisasterMode(): DisasterMode {
    const disaster: DisasterMode = {
      status: 'INACTIVE',
    };

    writeStorage(DISASTER_KEY, disaster);

    createEvent(
      'DISASTER_DEACTIVATED',
      'Disaster mode deactivated',
      'Emergency disaster mode has been closed.'
    );

    return disaster;
  },

  // ==========================================================
  // AUTHORIZED VEHICLE REGISTRY
  // ==========================================================

  getAuthorizedVehicles(): AuthorizedVehicle[] {
    return readStorage<AuthorizedVehicle[]>(VEHICLES_KEY, []);
  },

  registerVehicle(data: {
    vehicleId: string;
    vehicleType: VehicleType;
    licensePlate: string;
    authority: AuthorizedVehicle['authority'];
    registeredBy?: string;
  }): AuthorizedVehicle {
    const vehicles = this.getAuthorizedVehicles();

    const existing = vehicles.find(
      (vehicle) =>
        vehicle.vehicleId.toUpperCase() ===
        data.vehicleId.trim().toUpperCase()
    );

    if (existing) {
      if (!existing.authorized) {
        existing.authorized = true;
        existing.registeredAt = new Date().toISOString();

        writeStorage(VEHICLES_KEY, vehicles);

        createEvent(
          'VEHICLE_REGISTERED',
          'Vehicle authorization restored',
          `Vehicle ${existing.vehicleId} is authorized again.`,
          existing.vehicleId
        );
      }

      return existing;
    }

    const vehicle: AuthorizedVehicle = {
      id: `c2-vehicle-${Date.now()}`,
      vehicleId: data.vehicleId.trim().toUpperCase(),
      vehicleType: data.vehicleType,
      licensePlate: data.licensePlate,
      authority: data.authority,
      authorized: true,
      registeredAt: new Date().toISOString(),
      registeredBy: data.registeredBy,
    };

    writeStorage(VEHICLES_KEY, [...vehicles, vehicle]);

    createEvent(
      'VEHICLE_REGISTERED',
      'Vehicle registered',
      `Vehicle ${vehicle.vehicleId} has been authorized.`,
      vehicle.vehicleId
    );

    return vehicle;
  },

  revokeVehicle(vehicleId: string): boolean {
    const vehicles = this.getAuthorizedVehicles();

    const vehicle = vehicles.find(
      (item) =>
        item.vehicleId.toUpperCase() === vehicleId.trim().toUpperCase()
    );

    if (!vehicle) {
      return false;
    }

    vehicle.authorized = false;

    writeStorage(VEHICLES_KEY, vehicles);

    createEvent(
      'VEHICLE_REVOKED',
      'Vehicle authorization revoked',
      `Vehicle ${vehicle.vehicleId} is no longer authorized.`,
      vehicle.vehicleId
    );

    return true;
  },

  isVehicleAuthorized(vehicleId: string): boolean {
    return this.getAuthorizedVehicles().some(
      (vehicle) =>
        vehicle.vehicleId.toUpperCase() === vehicleId.trim().toUpperCase() &&
        vehicle.authorized
    );
  },

  // ==========================================================
  // EVENTS
  // ==========================================================

  getEvents(): C2Event[] {
    return readStorage<C2Event[]>(EVENTS_KEY, []);
  },

  clearEvents(): void {
    writeStorage(EVENTS_KEY, []);
  },

  recordEmergencyStarted(vehicle: EmergencyVehicle) {
    createEvent(
      'EMERGENCY_STARTED',
      'Emergency started',
      `${vehicle.type} ${vehicle.id} started an emergency journey.`,
      vehicle.id
    );
  },

  recordEmergencyCompleted(vehicle: EmergencyVehicle) {
    createEvent(
      'EMERGENCY_COMPLETED',
      'Emergency completed',
      `${vehicle.type} ${vehicle.id} reached its destination.`,
      vehicle.id
    );
  },

  // ==========================================================
  // PERFORMANCE
  // ==========================================================

  getPerformance(
    emergencyVehicles: EmergencyVehicle[]
  ): C2Performance {
    const events = this.getEvents();
    const vehicles = this.getAuthorizedVehicles();

    const activeEmergencies = emergencyVehicles.filter(
      (vehicle) =>
        Number(vehicle.progressPercent) < 100
    ).length;

    const completedEmergencies = events.filter(
      (event) => event.type === 'EMERGENCY_COMPLETED'
    ).length;

    const etaValues = emergencyVehicles
      .map((vehicle) => Number(vehicle.remainingEtaMinutes))
      .filter((value) => Number.isFinite(value));

    const averageEtaMinutes =
      etaValues.length > 0
        ? Number(
            (
              etaValues.reduce((sum, value) => sum + value, 0) /
              etaValues.length
            ).toFixed(1)
          )
        : 0;

    return {
      totalEvents: events.length,
      activeEmergencies,
      completedEmergencies,
      authorizedVehicles: vehicles.filter(
        (vehicle) => vehicle.authorized
      ).length,
      revokedVehicles: vehicles.filter(
        (vehicle) => !vehicle.authorized
      ).length,
      averageEtaMinutes,
    };
  },
};