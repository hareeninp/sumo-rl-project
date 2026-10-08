import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

import {
  User,
  EmergencyVehicle,
  NormalVehicle,
  Scenario,
  RouteOption,
  TurnInstruction,
  GPSAccuracyStatus,
  DisasterMode,
  AuthorizedVehicle,
  C2Event,
  C2Performance,
} from './types';

import { MOCK_JUNCTIONS } from './data/mock/mockJunctions';
import { MOCK_ROADS } from './data/mock/mockRoads';
import { MOCK_HOSPITALS } from './data/mock/mockHospitals';
import { MOCK_NORMAL_VEHICLES } from './data/mock/mockVehicles';
import { MOCK_SCENARIOS } from './data/mock/mockScenarios';

import { authService } from './services/authService';
import { geoService } from './services/geoService';
import { navigationService } from './services/navigationService';
import { routingService } from './services/routingService';
import { team1Service } from './services/team1Service';
import { c2Service } from './services/c2Service';

import { Header } from './components/Header';
import { OpeningPage } from './components/OpeningPage';
import { VehicleDetailsPage } from './components/VehicleDetailsPage';

import { AmbulanceEmergencyForm } from './components/AmbulanceEmergencyForm';
import { FireEmergencyForm } from './components/FireEmergencyForm';
import { PoliceEmergencyForm } from './components/PoliceEmergencyForm';

import { RouteCalculationModal } from './components/RouteCalculationModal';

import { EmergencyMap } from './components/EmergencyMap';

import { ActiveEmergenciesPanel } from './components/ActiveEmergenciesPanel';
import { RouteInfoCard } from './components/RouteInfoCard';
import { MapControls } from './components/MapControls';
import { BottomNavigationSummary } from './components/BottomNavigationSummary';

import { ArrivalModal } from './components/ArrivalModal';
import { PriorityScoreModal } from './components/PriorityScoreModal';
import { ScenarioSelector } from './components/ScenarioSelector';
import { TurnByTurnBar } from './components/TurnByTurnBar';

import { DisasterModePanel } from './components/DisasterModePanel';
import { AuthorizedVehicleRegistry } from './components/AuthorizedVehicleRegistry';
import { EventTimeline } from './components/EventTimeline';
import { PerformanceDashboard } from './components/PerformanceDashboard';

// ============================================================
// PAGE STATE
// ============================================================

type PageState =
  | 'OPENING'
  | 'VEHICLE_DETAILS'
  | 'EMERGENCY_FORM'
  | 'CALCULATING'
  | 'MAP_NAVIGATION';

// ============================================================
// INITIAL VEHICLE
// ============================================================

const INITIAL_EMERGENCY_VEHICLE: EmergencyVehicle = {
  id: 'AMB-01',
  name: 'Ambulance AMB-01',
  type: 'ambulance',
  licensePlate: 'TN-01-AB-1234',
  priority: 'high',
  startJunctionId: 'J1',
  destinationName: 'Metro General Hospital',
  destinationJunctionId: 'J7',
  selectedHospitalId: 'H1',
  patientCondition: 'General Emergency',
  currentJunctionId: 'J1',
  progressPercent: 0,
  speedKmh: 48,
  headingDeg: 45,
  priorityScore: 92,
  priorityStatus: 'FAVOURED',
  greenCorridorActive: true,
  accumulatedDelayMin: 0,
  currentRoadId: 'R_J1_J2',
  latitude: 37.7842,
  longitude: -122.4285,
  remainingDistanceKm: 3.2,
  remainingEtaMinutes: 5.5,
  route: {
    id: 'route-initial',
    name: 'Recommended Route',
    isRecommended: true,
    pathJunctionIds: ['J1', 'J2', 'J7'],
    totalDistanceKm: 3.2,
    etaMinutes: 5.5,
    trafficSummary: 'Clear',
    greenCorridorSupported: true,
    reasons: [
      'Lowest estimated travel time',
      'Avoids heavy traffic',
      'Green corridor available',
      'Direct arterial path',
    ],
    color: '#10b981',
  },
  alternateRoutes: [
    {
      id: 'route-alt-1',
      name: 'Alternate Route 1',
      isRecommended: false,
      pathJunctionIds: ['J1', 'J6', 'J7'],
      totalDistanceKm: 3.5,
      etaMinutes: 6.8,
      trafficSummary: 'Moderate',
      greenCorridorSupported: true,
      reasons: ['Alternative path', 'Avoids peak junction queues'],
      color: '#3b82f6',
    },
    {
      id: 'route-alt-2',
      name: 'Alternate Route 2',
      isRecommended: false,
      pathJunctionIds: ['J1', 'J2', 'J3', 'J8', 'J7'],
      totalDistanceKm: 4.8,
      etaMinutes: 9.0,
      trafficSummary: 'Heavy',
      greenCorridorSupported: false,
      reasons: ['Longer distance', 'Higher traffic along bypass'],
      color: '#f59e0b',
    },
  ],
};

// ============================================================
// APP
// ============================================================

export default function App() {
  // ==========================================================
  // AUTH
  // ==========================================================

  const [currentUser, setCurrentUser] = useState<User | null>(() =>
    authService.restoreSession()
  );

  const [pageState, setPageState] = useState<PageState>(() => {
    const saved = authService.restoreSession();
    return saved ? 'EMERGENCY_FORM' : 'OPENING';
  });

  // ==========================================================
  // VEHICLES
  // ==========================================================

  const [emergencyVehicles, setEmergencyVehicles] = useState<
    EmergencyVehicle[]
  >([INITIAL_EMERGENCY_VEHICLE]);

  const [activeVehicleId, setActiveVehicleId] = useState<string>(
    INITIAL_EMERGENCY_VEHICLE.id
  );

  const [normalVehicles, setNormalVehicles] = useState<NormalVehicle[]>(
    MOCK_NORMAL_VEHICLES
  );

  const [activeScenario, setActiveScenario] = useState<Scenario>(
    MOCK_SCENARIOS[0]
  );

  // ==========================================================
  // TRAFFIC
  // ==========================================================

  const [trafficData, setTrafficData] = useState<any[]>([]);
  const [_trafficLoading, setTrafficLoading] = useState(false);

  // ==========================================================
  // NAVIGATION & UI
  // ==========================================================

  const [isNavigating, setIsNavigating] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [isSimpleMode, setIsSimpleMode] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [showArrivalModal, setShowArrivalModal] = useState(false);
  const [showPriorityModal, setShowPriorityModal] = useState(false);
  const [showRouteCard, setShowRouteCard] = useState(true);
  const [showTraffic, setShowTraffic] = useState(true);
  const [showGreenCorridor, setShowGreenCorridor] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1.0);

  // ==========================================================
  // C2 - DISASTER / REGISTRY / DASHBOARD
  // ==========================================================

  const [disasterMode, setDisasterMode] =
    useState<DisasterMode>(() =>
      c2Service.getDisasterMode()
    );

  const [authorizedVehicles, setAuthorizedVehicles] =
    useState<AuthorizedVehicle[]>(() =>
      c2Service.getAuthorizedVehicles()
    );

  const [c2Events, setC2Events] =
    useState<C2Event[]>(() =>
      c2Service.getEvents()
    );

  const [c2Performance, setC2Performance] =
    useState<C2Performance>(() =>
      c2Service.getPerformance([])
    );

  const [showC2Dashboard, setShowC2Dashboard] =
    useState(false);

  const refreshC2 = useCallback(() => {
    const vehicles = c2Service.getAuthorizedVehicles();
    const events = c2Service.getEvents();

    setDisasterMode(c2Service.getDisasterMode());
    setAuthorizedVehicles(vehicles);
    setC2Events(events);
    setC2Performance(
      c2Service.getPerformance(emergencyVehicles)
    );
  }, [emergencyVehicles]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      refreshC2();
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [refreshC2]);

  // ==========================================================
  // GPS
  // ==========================================================

  const [gpsStatus, setGpsStatus] = useState<GPSAccuracyStatus>('STRONG');
  const animationFrameRef = useRef<number | null>(null);

  // ==========================================================
  // ARRIVAL FLAG
  // ==========================================================

  const arrivalHandledRef = useRef(false);

  // ==========================================================
  // SUMO TRAFFIC FETCH
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    const fetchTraffic = async () => {
      setTrafficLoading(true);
      try {
        const response = await fetch('http://127.0.0.1:5000/api/traffic');
        if (!response.ok) {
          throw new Error(`Traffic API returned ${response.status}`);
        }
        const result = await response.json();
        if (!cancelled && result.success) {
          setTrafficData(result.data || []);
        }
      } catch {
        if (!cancelled) {
          setTrafficData([]);
        }
      } finally {
        if (!cancelled) {
          setTrafficLoading(false);
        }
      }
    };

    fetchTraffic();
    const interval = window.setInterval(fetchTraffic, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  // ==========================================================
  // GPS WATCHER
  // ==========================================================

  useEffect(() => {
    geoService.watchPosition((state) => {
      setGpsStatus(state.status === 'MEDIUM' ? 'WEAK' : state.status);
    });

    return () => {
      geoService.stopWatching();
    };
  }, []);

  // ==========================================================
  // ACTIVE VEHICLE
  // ==========================================================

  const activeVehicle =
    emergencyVehicles.find((v) => v.id === activeVehicleId) ||
    emergencyVehicles[0];

  // ==========================================================
  // TURN INSTRUCTION
  // ==========================================================

  const currentInstruction: TurnInstruction = activeVehicle?.route
    ? navigationService.getNextInstruction(
        activeVehicle.route,
        activeVehicle.progressPercent
      )
    : {
        id: 'inst-default',
        instruction: 'Proceed to emergency destination',
        maneuver: 'straight',
        distanceMeters: 450,
        junctionId: 'J1',
        roadName: 'Main Arterial Corridor',
      };

  // ==========================================================
  // PROGRESS & DISTANCE & ETA
  // ==========================================================

  const routeProgress = activeVehicle
    ? Math.max(0, Math.min(100, Number(activeVehicle.progressPercent) || 0))
    : 0;

  const remainingKm = activeVehicle?.route
    ? routeProgress >= 100
      ? 0
      : Number(
          Math.max(
            0,
            activeVehicle.route.totalDistanceKm * (1 - routeProgress / 100)
          ).toFixed(1)
        )
    : 0;

  const remainingETA = activeVehicle?.route
    ? routeProgress >= 100
      ? 0
      : Number(
          Math.max(
            0,
            activeVehicle.route.etaMinutes * (1 - routeProgress / 100)
          ).toFixed(1)
        )
    : 0;

  // ==========================================================
  // 🚑 FINITE REAL NAVIGATION SIMULATION
  //
  // 0 → 100%
  // Stops permanently at destination
  // Never resets to 0% for emergency vehicle
  // ==========================================================

  useEffect(() => {
    if (pageState !== 'MAP_NAVIGATION' || !isNavigating) {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      return;
    }

    let lastTimestamp = performance.now();

    const updateSimulation = (now: number) => {
      const deltaSec = Math.min((now - lastTimestamp) / 1000, 0.1);
      lastTimestamp = now;

      // ======================================================
      // NORMAL VEHICLES (Background traffic loops)
      // ======================================================

      setNormalVehicles((prev) =>
        prev.map((vehicle) => {
          let nextProgress = vehicle.progressPercent + deltaSec * 4;
          if (nextProgress >= 100) {
            nextProgress = 0;
          }
          return {
            ...vehicle,
            progressPercent: nextProgress,
          };
        })
      );

      // ======================================================
      // ACTIVE EMERGENCY VEHICLE (Finite trip: 0 -> 100% -> STOP)
      // ======================================================

      setEmergencyVehicles((prev) =>
        prev.map((vehicle) => {
          if (vehicle.id !== activeVehicleId) {
            return vehicle;
          }

          const route = vehicle.route;
          if (!route || !route.pathJunctionIds || route.pathJunctionIds.length === 0) {
            return vehicle;
          }

          const currentProgress = Math.max(
            0,
            Math.min(100, Number(vehicle.progressPercent) || 0)
          );

          const destJunctionId =
            route.pathJunctionIds[route.pathJunctionIds.length - 1];
          const destJunction = MOCK_JUNCTIONS.find(
            (j) => j.id === destJunctionId
          );

          // If already at 100%: handle arrival once and stop
          if (currentProgress >= 100) {
            if (!arrivalHandledRef.current) {
              arrivalHandledRef.current = true;
              navigationService.endNavigation();
              setIsNavigating(false);
              if (activeVehicle) {
                c2Service.recordEmergencyCompleted(
                  activeVehicle
                );
              }
              setShowArrivalModal(true);
            }

            return {
              ...vehicle,
              progressPercent: 100,
              speedKmh: 0,
              remainingDistanceKm: 0,
              remainingEtaMinutes: 0,
              currentJunctionId: destJunctionId,
              latitude: destJunction?.latitude ?? vehicle.latitude,
              longitude: destJunction?.longitude ?? vehicle.longitude,
            };
          }

          // Advance progress (0.8% per second -> smooth, realistic pace)
          const movementSpeed = 0.8;
          let nextProgress = currentProgress + deltaSec * movementSpeed;

          // Clamp to 100 max
          if (nextProgress >= 100) {
            nextProgress = 100;

            if (!arrivalHandledRef.current) {
              arrivalHandledRef.current = true;
              navigationService.endNavigation();
              setIsNavigating(false);
              setShowArrivalModal(true);
            }

            return {
              ...vehicle,
              progressPercent: 100,
              speedKmh: 0,
              remainingDistanceKm: 0,
              remainingEtaMinutes: 0,
              currentJunctionId: destJunctionId,
              latitude: destJunction?.latitude ?? vehicle.latitude,
              longitude: destJunction?.longitude ?? vehicle.longitude,
            };
          }

          // Calculate current road segment and interpolated coordinates matching GoogleMapView
          const path = route.pathJunctionIds;
          const segmentLengths: number[] = [];
          let totalSegmentDistance = 0;

          for (let i = 0; i < path.length - 1; i++) {
            const fromId = path[i];
            const toId = path[i + 1];
            const road = MOCK_ROADS.find(
              (r) =>
                (r.fromJunction === fromId && r.toJunction === toId) ||
                (r.fromJunction === toId && r.toJunction === fromId)
            );
            const fromJunc = MOCK_JUNCTIONS.find((j) => j.id === fromId);
            const toJunc = MOCK_JUNCTIONS.find((j) => j.id === toId);
            const coordLen =
              fromJunc && toJunc
                ? Math.hypot(
                    toJunc.longitude - fromJunc.longitude,
                    toJunc.latitude - fromJunc.latitude
                  )
                : 10;
            const segDist = road?.lengthKm && road.lengthKm > 0 ? road.lengthKm : Math.max(coordLen / 10, 0.1);
            segmentLengths.push(segDist);
            totalSegmentDistance += segDist;
          }

          let currentLat = vehicle.latitude;
          let currentLng = vehicle.longitude;
          let currentJuncId = path[0];

          if (totalSegmentDistance > 0) {
            const travelled = (nextProgress / 100) * totalSegmentDistance;
            let accumulated = 0;

            for (let i = 0; i < segmentLengths.length; i++) {
              const segLen = segmentLengths[i];
              const segEnd = accumulated + segLen;

              if (travelled <= segEnd || i === segmentLengths.length - 1) {
                const localRatio = segLen > 0 ? Math.max(0, Math.min(1, (travelled - accumulated) / segLen)) : 0;
                const fromJunc = MOCK_JUNCTIONS.find((j) => j.id === path[i]);
                const toJunc = MOCK_JUNCTIONS.find((j) => j.id === path[i + 1]);

                currentJuncId = path[i];
                if (fromJunc && toJunc) {
                  currentLat = fromJunc.latitude + (toJunc.latitude - fromJunc.latitude) * localRatio;
                  currentLng = fromJunc.longitude + (toJunc.longitude - fromJunc.longitude) * localRatio;
                }
                break;
              }
              accumulated += segLen;
            }
          }

          const remKm = Number(
            Math.max(
              0,
              route.totalDistanceKm * (1 - nextProgress / 100)
            ).toFixed(1)
          );

          const remEta = Number(
            Math.max(0, route.etaMinutes * (1 - nextProgress / 100)).toFixed(1)
          );

          return {
            ...vehicle,
            progressPercent: nextProgress,
            speedKmh: 52,
            currentJunctionId: currentJuncId,
            latitude: currentLat,
            longitude: currentLng,
            remainingDistanceKm: remKm,
            remainingEtaMinutes: remEta,
          };
        })
      );

      // Continue animation loop while navigating
      if (isNavigating) {
        animationFrameRef.current = requestAnimationFrame(updateSimulation);
      }
    };

    animationFrameRef.current = requestAnimationFrame(updateSimulation);

    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [pageState, isNavigating, activeVehicleId]);

  // ==========================================================
  // SAVE USER
  // ==========================================================

  const handleSaveUser = (user: User) => {
    setCurrentUser(user);

    if (user.rememberDevice) {
      authService.login(user.vehicleId, '', user.vehicleType, true);
    }

    setPageState('EMERGENCY_FORM');
  };

  // ==========================================================
  // LOGOUT
  // ==========================================================

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    setIsNavigating(false);
    setShowArrivalModal(false);
    arrivalHandledRef.current = false;
    navigationService.endNavigation();
    setPageState('OPENING');
  };

  // ==========================================================
  // NEW EMERGENCY
  // ==========================================================

  const handleNavigateNewEmergency = () => {
    setShowArrivalModal(false);
    setIsNavigating(false);
    arrivalHandledRef.current = false;
    navigationService.endNavigation();
    setPageState('EMERGENCY_FORM');
  };

  // ==========================================================
  // BACK NAVIGATION
  // ==========================================================

  const handleGoBack = () => {
    if (pageState === 'MAP_NAVIGATION' || pageState === 'CALCULATING') {
      setIsNavigating(false);
      setShowArrivalModal(false);
      arrivalHandledRef.current = false;
      navigationService.endNavigation();
      setPageState('EMERGENCY_FORM');
    } else if (pageState === 'EMERGENCY_FORM') {
      setPageState('VEHICLE_DETAILS');
    } else if (pageState === 'VEHICLE_DETAILS') {
      setPageState('OPENING');
    }
  };

  // ==========================================================
  // ROUTE CALCULATION COMPLETE -> START NAVIGATION
  // ==========================================================

  const handleCalculationComplete = useCallback(() => {
    arrivalHandledRef.current = false;
    setShowArrivalModal(false);
    setIsNavigating(false);
    navigationService.endNavigation();
    setPageState('MAP_NAVIGATION');
  }, []);

  const handleCalculationCancel = useCallback(() => {
    handleGoBack();
  }, [pageState]);

  // ==========================================================
  // EMERGENCY FORM SUBMIT
  // ==========================================================

  const handleEmergencySubmit = (data: {
    destinationName: string;
    destinationJunctionId: string;
    priority: 'high' | 'medium' | 'low';
    startLocationJunctionId: string;
    patientCondition?: string;
    isUsingLiveGps?: boolean;
    liveGpsCoords?: {
      lat: number;
      lng: number;
    };
  }) => {
    if (!currentUser) return;

    const { recommended, alternates } = routingService.calculateBestRoute(
      data.startLocationJunctionId,
      data.destinationJunctionId,
      currentUser.vehicleType,
      data.patientCondition || data.destinationName,
      data.priority
    );

    const startJunc = MOCK_JUNCTIONS.find(
      (j) => j.id === data.startLocationJunctionId
    );

    const newVehicle: EmergencyVehicle = {
      id: currentUser.vehicleId,
      name:
        currentUser.vehicleType === 'ambulance'
          ? `Ambulance ${currentUser.vehicleId}`
          : currentUser.vehicleType === 'fireEngine'
          ? `Fire Engine ${currentUser.vehicleId}`
          : `Police Unit ${currentUser.vehicleId}`,
      type: currentUser.vehicleType,
      licensePlate: currentUser.licenseNumber,
      priority: data.priority,
      startJunctionId: data.startLocationJunctionId,
      destinationName: data.destinationName,
      destinationJunctionId: data.destinationJunctionId,
      patientCondition: data.patientCondition,
      currentJunctionId: data.startLocationJunctionId,
      progressPercent: 0,
      speedKmh: 48,
      headingDeg: 45,
      priorityScore:
        data.priority === 'high' ? 92 : data.priority === 'medium' ? 76 : 58,
      priorityStatus: 'FAVOURED',
      greenCorridorActive: true,
      accumulatedDelayMin: 0,
      latitude: startJunc?.latitude,
      longitude: startJunc?.longitude,
      remainingDistanceKm: recommended.totalDistanceKm,
      remainingEtaMinutes: recommended.etaMinutes,
      route: recommended,
      alternateRoutes: alternates || [],
      liveGps: data.liveGpsCoords
        ? {
            lat: data.liveGpsCoords.lat,
            lng: data.liveGpsCoords.lng,
            accuracyMeters: 8,
            isReal: true,
          }
        : undefined,
    };

    arrivalHandledRef.current = false;
    setEmergencyVehicles([newVehicle]);
    setActiveVehicleId(newVehicle.id);

    c2Service.recordEmergencyStarted(newVehicle);

    setShowRouteCard(true);
    setShowArrivalModal(false);
    setIsNavigating(false);
    setPageState('CALCULATING');
  };

  // ==========================================================
  // C2 - DISASTER MODE
  // ==========================================================

  const handleActivateDisaster = (
    type: string,
    description: string
  ) => {
    const userName =
      currentUser?.officerName ||
      currentUser?.vehicleId ||
      'System';

    const updated = c2Service.activateDisasterMode(
      type,
      description,
      userName
    );

    setDisasterMode(updated);
    setC2Events(c2Service.getEvents());
  };

  const handleDeactivateDisaster = () => {
    const updated =
      c2Service.deactivateDisasterMode();

    setDisasterMode(updated);
    setC2Events(c2Service.getEvents());
  };

  // ==========================================================
  // C2 - VEHICLE REGISTRY
  // ==========================================================

  const handleRegisterVehicle = (data: {
    vehicleId: string;
    vehicleType:
      | 'ambulance'
      | 'fireEngine'
      | 'police';
    licensePlate: string;
    authority:
      | 'police'
      | 'hospital'
      | 'disaster_authority';
  }) => {
    c2Service.registerVehicle({
      ...data,
      registeredBy:
        currentUser?.officerName ||
        currentUser?.vehicleId ||
        'System',
    });

    refreshC2();
  };

  const handleRevokeVehicle = (
    vehicleId: string
  ) => {
    c2Service.revokeVehicle(vehicleId);
    refreshC2();
  };

  // ==========================================================
  // SCENARIO SELECTION
  // ==========================================================

  const handleSelectScenario = (sc: Scenario) => {
    setActiveScenario(sc);

    setEmergencyVehicles(
      sc.vehicles.map((vehicle) => {
        const startJunc = MOCK_JUNCTIONS.find(
          (j) => j.id === (vehicle.route?.pathJunctionIds?.[0] || vehicle.startJunctionId)
        );

        return {
          ...vehicle,
          progressPercent: 0,
          alternateRoutes: vehicle.alternateRoutes || [],
          latitude: vehicle.latitude || startJunc?.latitude,
          longitude: vehicle.longitude || startJunc?.longitude,
          remainingDistanceKm:
            vehicle.route?.totalDistanceKm ?? vehicle.remainingDistanceKm,
          remainingEtaMinutes:
            vehicle.route?.etaMinutes ?? vehicle.remainingEtaMinutes,
        };
      })
    );

    if (sc.vehicles[0]) {
      setActiveVehicleId(sc.vehicles[0].id);
    }

    arrivalHandledRef.current = false;
    setIsNavigating(false);
    setShowArrivalModal(false);
    setShowRouteCard(true);
  };

  // ==========================================================
  // ROUTE SWITCHING
  // ==========================================================

  const handleSelectRoute = (newRoute: RouteOption) => {
    arrivalHandledRef.current = false;
    setShowArrivalModal(false);
    setIsNavigating(false);
    navigationService.endNavigation();

    setEmergencyVehicles((prev) =>
      prev.map((vehicle) => {
        if (vehicle.id !== activeVehicleId) {
          return vehicle;
        }

        const startJunc = MOCK_JUNCTIONS.find(
          (j) => j.id === newRoute.pathJunctionIds[0]
        );

        return {
          ...vehicle,
          route: newRoute,
          progressPercent: 0,
          speedKmh: 48,
          currentJunctionId: newRoute.pathJunctionIds[0],
          latitude: startJunc?.latitude ?? vehicle.latitude,
          longitude: startJunc?.longitude ?? vehicle.longitude,
          remainingDistanceKm: newRoute.totalDistanceKm,
          remainingEtaMinutes: newRoute.etaMinutes,
        };
      })
    );
  };

  // ==========================================================
  // START / END NAVIGATION TOGGLE
  // ==========================================================

  const handleToggleNavigation = useCallback(() => {
    try {
      if (isNavigating) {
        navigationService.endNavigation();
        setIsNavigating(false);
        return;
      }

      // If already arrived (progress >= 100), reset to start position and start fresh
      if (activeVehicle && Number(activeVehicle.progressPercent) >= 100) {
        const startJunc = MOCK_JUNCTIONS.find(
          (j) => j.id === (activeVehicle.route?.pathJunctionIds?.[0] || activeVehicle.startJunctionId)
        );

        setEmergencyVehicles((prev) =>
          prev.map((v) =>
            v.id === activeVehicle.id
              ? {
                  ...v,
                  progressPercent: 0,
                  speedKmh: 52,
                  remainingDistanceKm: v.route?.totalDistanceKm ?? 3.2,
                  remainingEtaMinutes: v.route?.etaMinutes ?? 5.5,
                  currentJunctionId: v.route?.pathJunctionIds?.[0] ?? v.startJunctionId,
                  latitude: startJunc?.latitude ?? v.latitude,
                  longitude: startJunc?.longitude ?? v.longitude,
                }
              : v
          )
        );
      }

      arrivalHandledRef.current = false;
      setShowArrivalModal(false);
      navigationService.startNavigation();
      setIsNavigating(true);
    } catch (error) {
      console.error('Failed to toggle navigation:', error);
      setIsNavigating(false);
    }
  }, [isNavigating, activeVehicle]);

  // ==========================================================
  // VOICE GUIDANCE TOGGLE
  // ==========================================================

  const handleToggleVoice = () => {
    const updated = navigationService.toggleVoice();
    setIsVoiceEnabled(updated);
  };

  // ==========================================================
  // REROUTE TRIGGER
  // ==========================================================

  const handleTriggerReroute = () => {
    setIsRecalculating(true);
    if (activeVehicle) {
      const { recommended } = routingService.calculateBestRoute(
        activeVehicle.currentJunctionId,
        activeVehicle.destinationJunctionId,
        activeVehicle.type,
        activeVehicle.destinationName,
        activeVehicle.priority
      );
      handleSelectRoute(recommended);
    }
    setIsRecalculating(false);
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans antialiased overflow-x-hidden selection:bg-blue-600 selection:text-white">
      {/* HEADER */}
      <Header
        user={currentUser}
        onLogout={handleLogout}
        onNavigateNewEmergency={handleNavigateNewEmergency}
        gpsStatus={gpsStatus}
        onBack={handleGoBack}
        canGoBack={pageState !== 'OPENING'}
      />

      {currentUser && (
        <button
          type="button"
          onClick={() =>
            setShowC2Dashboard((value) => !value)
          }
          className="fixed top-20 right-4 z-50 rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 text-sm font-bold text-white shadow-lg"
        >
          {showC2Dashboard
            ? 'Close C2 Dashboard'
            : 'C2 Dashboard'}
        </button>
      )}

      {showC2Dashboard && currentUser && (
        <div className="fixed inset-0 z-40 overflow-y-auto bg-slate-950/95 p-4 pt-28">
          <div className="mx-auto max-w-7xl space-y-5">

            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">
                  C2 Disaster Operations Dashboard
                </h1>

                <p className="text-sm text-slate-400">
                  Disaster mode, authorized vehicles,
                  event timeline and performance
                </p>
              </div>

              <button
                onClick={() =>
                  setShowC2Dashboard(false)
                }
                className="rounded-lg bg-slate-700 hover:bg-slate-600 px-4 py-2 text-sm font-semibold"
              >
                Close
              </button>
            </div>

            <PerformanceDashboard
              performance={c2Performance}
            />

            <DisasterModePanel
              disaster={disasterMode}
              onActivate={handleActivateDisaster}
              onDeactivate={handleDeactivateDisaster}
            />

            <AuthorizedVehicleRegistry
              vehicles={authorizedVehicles}
              onRegister={handleRegisterVehicle}
              onRevoke={handleRevokeVehicle}
            />

            <EventTimeline
              events={c2Events}
            />

          </div>
        </div>
      )}

      {/* OPENING */}
      {pageState === 'OPENING' && (
        <OpeningPage
          onGetStarted={() => setPageState('VEHICLE_DETAILS')}
          onQuickLogin={() => {
            const saved = authService.restoreSession();
            if (saved) {
              setCurrentUser(saved);
              setPageState('EMERGENCY_FORM');
            } else {
              setPageState('VEHICLE_DETAILS');
            }
          }}
          hasSavedSession={authService.isAuthenticated()}
          savedVehicleId={currentUser?.vehicleId}
        />
      )}

      {/* VEHICLE DETAILS */}
      {pageState === 'VEHICLE_DETAILS' && (
        <VehicleDetailsPage
          onBack={() => setPageState('OPENING')}
          onSaveAndProceed={handleSaveUser}
          initialUser={currentUser}
        />
      )}

      {/* EMERGENCY FORM */}
      {pageState === 'EMERGENCY_FORM' && currentUser && (
        <div className="grow bg-slate-50 py-6 sm:py-10">
          {currentUser.vehicleType === 'ambulance' && (
            <AmbulanceEmergencyForm
              user={currentUser}
              onBack={handleGoBack}
              onSubmit={handleEmergencySubmit}
            />
          )}

          {currentUser.vehicleType === 'fireEngine' && (
            <FireEmergencyForm
              user={currentUser}
              onBack={handleGoBack}
              onSubmit={handleEmergencySubmit}
            />
          )}

          {currentUser.vehicleType === 'police' && (
            <PoliceEmergencyForm
              user={currentUser}
              onBack={handleGoBack}
              onSubmit={handleEmergencySubmit}
            />
          )}
        </div>
      )}

      {/* ROUTE CALCULATING ANIMATION */}
      {pageState === 'CALCULATING' && (
        <RouteCalculationModal
          onComplete={handleCalculationComplete}
          onCancel={handleCalculationCancel}
        />
      )}

      {/* MAP NAVIGATION */}
      {pageState === 'MAP_NAVIGATION' && (
        <main className="relative grow w-full h-[calc(100vh-61px)] overflow-hidden flex flex-col">
          {/* TURN BY TURN */}
          {activeVehicle && (
            <TurnByTurnBar
              instruction={currentInstruction}
              isVoiceEnabled={isVoiceEnabled}
              onToggleVoice={handleToggleVoice}
              isRecalculating={isRecalculating}
              onBack={handleGoBack}
            />
          )}

          {/* EMERGENCY MAP */}
          <div className="w-full h-full flex-1 min-h-0">
            <EmergencyMap
              junctions={MOCK_JUNCTIONS}
              roads={MOCK_ROADS}
              hospitals={MOCK_HOSPITALS}
              emergencyVehicles={emergencyVehicles}
              normalVehicles={normalVehicles}
              trafficData={trafficData}
              activeVehicleId={activeVehicleId}
              onSelectVehicle={(id) => {
                setActiveVehicleId(id);
                setShowRouteCard(true);
              }}
              showTraffic={showTraffic}
              showGreenCorridor={showGreenCorridor}
              weather={team1Service.getWeatherData()}
              zoomLevel={zoomLevel}
              isNavigating={isNavigating}
              isSimpleMode={isSimpleMode}
            />
          </div>

          {/* ACTIVE EMERGENCIES PANEL */}
          {!isSimpleMode && emergencyVehicles.length > 1 && (
            <div className="absolute top-24 left-4 z-20 hidden md:block">
              <ActiveEmergenciesPanel
                vehicles={emergencyVehicles}
                selectedVehicleId={activeVehicleId}
                onSelectVehicle={(id) => setActiveVehicleId(id)}
                onOpenPriorityFormula={() => setShowPriorityModal(true)}
              />
            </div>
          )}

          {/* ROUTE INFO CARD */}
          {!isSimpleMode && showRouteCard && activeVehicle && (
            <div className="absolute top-24 left-4 z-20 max-h-[calc(100vh-220px)] overflow-y-auto hidden sm:block">
              <RouteInfoCard
                vehicle={activeVehicle}
                onSelectRoute={handleSelectRoute}
              />
            </div>
          )}

          {/* MAP CONTROLS & SCENARIO SELECTOR */}
          <div className="absolute bottom-24 right-4 z-20 flex flex-col items-end gap-2">
            {!isSimpleMode && (
              <ScenarioSelector
                currentScenarioId={activeScenario.id}
                onSelectScenario={handleSelectScenario}
              />
            )}

            <MapControls
              onZoomIn={() =>
                setZoomLevel((z) => Math.min(1.8, +(z + 0.15).toFixed(2)))
              }
              onZoomOut={() =>
                setZoomLevel((z) => Math.max(0.75, +(z - 0.15).toFixed(2)))
              }
              onRecenter={() => setZoomLevel(1.0)}
              showTraffic={showTraffic}
              onToggleTraffic={() => setShowTraffic(!showTraffic)}
              showGreenCorridor={showGreenCorridor}
              onToggleGreenCorridor={() =>
                setShowGreenCorridor(!showGreenCorridor)
              }
              onNewEmergency={handleNavigateNewEmergency}
            />
          </div>

          {/* BOTTOM NAVIGATION SUMMARY */}
          {activeVehicle && (
            <BottomNavigationSummary
              vehicleType={activeVehicle.type}
              vehicleId={activeVehicle.id}
              etaMinutes={remainingETA}
              remainingDistanceKm={remainingKm}
              isNavigating={isNavigating}
              onToggleNavigation={handleToggleNavigation}
              isVoiceEnabled={isVoiceEnabled}
              onToggleVoice={handleToggleVoice}
              isSimpleMode={isSimpleMode}
              onToggleSimpleMode={() => setIsSimpleMode(!isSimpleMode)}
            />
          )}

          {/* ARRIVAL MODAL */}
          {showArrivalModal && activeVehicle && (
            <ArrivalModal
              vehicle={activeVehicle}
              onNewEmergency={handleNavigateNewEmergency}
            />
          )}

          {/* PRIORITY SCORE MODAL */}
          {showPriorityModal && (
            <PriorityScoreModal
              vehicles={emergencyVehicles}
              onClose={() => setShowPriorityModal(false)}
            />
          )}

          {/* HIDDEN REROUTE BUTTON */}
          <button
            type="button"
            onClick={handleTriggerReroute}
            className="sr-only"
            aria-label="Simulate route deviation recalculation"
          >
            Recalculate
          </button>
        </main>
      )}
    </div>
  );
}