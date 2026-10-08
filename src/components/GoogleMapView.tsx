import React, { useEffect, useMemo, useState } from 'react';

import {
  EmergencyVehicle,
  Hospital,
  Junction,
  Road,
  WeatherData,
} from '../types';

import {
  Ambulance,
  Flame,
  Siren,
  Building2,
  Radio,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  LocateFixed,
} from 'lucide-react';

interface SumoJunction {
  id: string;
  x: number;
  y: number;
  latitude?: number;
  longitude?: number;
  name?: string;
  signalState?: string;
  isMainJunction?: boolean;
}

interface SumoRoad {
  id: string;
  fromJunction: string;
  toJunction: string;
  laneCount?: number;
  lengthMeters?: number;
  speedLimitMs?: number;
  speedLimitKmh?: number;
  trafficLevel?: string;
  shape?: {
    x: number;
    y: number;
  }[];
}

interface SumoTrafficLight {
  id: string;
  junctionId: string;
  x: number | null;
  y: number | null;
  state: string;
  stateSummary: 'red' | 'yellow' | 'green';
  phase: number;
  phaseDuration: number;
  nextSwitch: number;
  controlledLanes: string[];
  controlledLaneCount: number;
  controlledLinkCount: number;
}

interface SumoNetworkResponse {
  success: boolean;
  junctions: SumoJunction[];
  roads: SumoRoad[];
  trafficLights?: SumoTrafficLight[];
  error?: string;
}

interface TrafficDataItem {
  junctionId: string;
  vehicleCount: number;
  queueLength: number;
  averageSpeed: number;
  averageSpeedKmh: number;
  signalPhase: number;
  signalState: string;
  stateSummary: 'red' | 'yellow' | 'green';
  phaseDuration: number;
  nextSwitch: number;
  controlledLanes: string[];
  controlledLaneCount: number;
}

interface TrafficResponse {
  success: boolean;
  simulationTime: number;
  data: TrafficDataItem[];
  error?: string;
}

interface UnifiedJunction {
  id: string;
  name: string;
  x: number;
  y: number;
  latitude: number;
  longitude: number;
  signalState?: string;
  preemptionStatus?: string;
}

interface UnifiedRoad {
  id: string;
  name?: string;
  fromJunction: string;
  toJunction: string;
  lengthKm: number;
  trafficLevel?: string;
  geometry?: Array<{
    latitude: number;
    longitude: number;
    x?: number;
    y?: number;
  }>;
}

interface GoogleMapViewProps {
  junctions: Junction[];
  roads: Road[];
  hospitals: Hospital[];
  activeVehicle: EmergencyVehicle;
  sumoVehicles?: any[];
  trafficData?: any[];
  showTraffic: boolean;
  showGreenCorridor: boolean;
  weather: WeatherData;
  zoomLevel: number;
  isNavigating: boolean;
  isSimpleMode: boolean;
  onOpenGoogleMapsExternal?: () => void;
}

export const GoogleMapView: React.FC<GoogleMapViewProps> = ({
  junctions: fallbackJunctions,
  roads: fallbackRoads,
  hospitals,
  activeVehicle,
  sumoVehicles: _sumoVehicles = [],
  trafficData: _trafficData = [],
  showTraffic,
  showGreenCorridor,
  weather: _weather,
  zoomLevel,
  isNavigating,
  isSimpleMode: _isSimpleMode,
}) => {
  const [sumoJunctions, setSumoJunctions] = useState<SumoJunction[]>([]);
  const [sumoRoads, setSumoRoads] = useState<SumoRoad[]>([]);
  const [sumoTrafficLights, setSumoTrafficLights] = useState<
    SumoTrafficLight[]
  >([]);

  const [sumoLoading, setSumoLoading] = useState(true);
  const [sumoError, setSumoError] = useState<string | null>(null);

  const [liveTraffic, setLiveTraffic] = useState<TrafficDataItem[]>([]);

  const [localZoom, setLocalZoom] = useState(
    Math.max(0.7, zoomLevel || 1)
  );

  useEffect(() => {
    if (zoomLevel) {
      setLocalZoom(zoomLevel);
    }
  }, [zoomLevel]);

  const increaseZoom = () => {
    setLocalZoom((previous) =>
      Math.min(3, Number((previous + 0.2).toFixed(2)))
    );
  };

  const decreaseZoom = () => {
    setLocalZoom((previous) =>
      Math.max(0.7, Number((previous - 0.2).toFixed(2)))
    );
  };

  const resetZoom = () => {
    setLocalZoom(1);
  };

  /*
   * ============================================================
   * LOAD SUMO NETWORK (IF AVAILABLE)
   * ============================================================
   */

  useEffect(() => {
    let cancelled = false;

    const loadSUMONetwork = async () => {
      try {
        setSumoLoading(true);
        setSumoError(null);

        const response = await fetch(
          'http://127.0.0.1:5000/api/network'
        );

        if (!response.ok) {
          throw new Error(`SUMO network API returned ${response.status}`);
        }

        const result: SumoNetworkResponse = await response.json();

        if (!result.success) {
          throw new Error(
            result.error || 'SUMO network request failed'
          );
        }

        if (!cancelled) {
          setSumoJunctions(result.junctions || []);
          setSumoRoads(result.roads || []);
          setSumoTrafficLights(result.trafficLights || []);
        }
      } catch (error) {
        if (!cancelled) {
          setSumoError(
            error instanceof Error
              ? error.message
              : 'Unable to connect to SUMO'
          );
          setSumoJunctions([]);
          setSumoRoads([]);
          setSumoTrafficLights([]);
        }
      } finally {
        if (!cancelled) {
          setSumoLoading(false);
        }
      }
    };

    loadSUMONetwork();

    return () => {
      cancelled = true;
    };
  }, []);

  /*
   * ============================================================
   * LOAD SUMO TRAFFIC (IF AVAILABLE)
   * ============================================================
   */

  useEffect(() => {
    let cancelled = false;

    const loadTraffic = async () => {
      try {
        const response = await fetch(
          'http://127.0.0.1:5000/api/traffic'
        );

        if (!response.ok) {
          return;
        }

        const result: TrafficResponse = await response.json();

        if (result.success && !cancelled) {
          setLiveTraffic(result.data || []);
        }
      } catch {
        // Standalone fallback
      }
    };

    loadTraffic();
    const interval = window.setInterval(loadTraffic, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const usingSUMO = sumoJunctions.length > 0;

  /*
   * ============================================================
   * UNIFIED NETWORK (SUMO OR MOCK DATA)
   * ============================================================
   */

  const bounds = useMemo(() => {
    if (sumoJunctions.length === 0) {
      return { minX: 0, maxX: 100, minY: 0, maxY: 100 };
    }

    const xs = sumoJunctions.map((j) => j.x);
    const ys = sumoJunctions.map((j) => j.y);

    const rawMinX = Math.min(...xs);
    const rawMaxX = Math.max(...xs);
    const rawMinY = Math.min(...ys);
    const rawMaxY = Math.max(...ys);

    const width = Math.max(1, rawMaxX - rawMinX);
    const height = Math.max(1, rawMaxY - rawMinY);

    return {
      minX: rawMinX - width * 0.08,
      maxX: rawMaxX + width * 0.08,
      minY: rawMinY - height * 0.08,
      maxY: rawMaxY + height * 0.08,
    };
  }, [sumoJunctions]);

  const toScreenX = (x: number): number => {
    if (!usingSUMO) return x;
    const width = bounds.maxX - bounds.minX;
    if (width === 0) return 50;
    return ((x - bounds.minX) / width) * 100;
  };

  const toScreenY = (y: number): number => {
    if (!usingSUMO) return y;
    const height = bounds.maxY - bounds.minY;
    if (height === 0) return 50;
    return 100 - ((y - bounds.minY) / height) * 100;
  };

  const unifiedJunctions: UnifiedJunction[] = useMemo(() => {
    if (usingSUMO) {
      return sumoJunctions.map((sj) => ({
        id: sj.id,
        name: sj.name || `Junction ${sj.id}`,
        x: toScreenX(sj.x),
        y: toScreenY(sj.y),
        latitude: sj.latitude || 37.7749,
        longitude: sj.longitude || -122.4194,
        signalState: sj.signalState || 'green',
        preemptionStatus: 'STANDBY',
      }));
    }

    return fallbackJunctions.map((fj) => ({
      id: fj.id,
      name: fj.name || `Junction ${fj.id}`,
      x: fj.x !== undefined ? fj.x : 50,
      y: fj.y !== undefined ? fj.y : 50,
      latitude: fj.latitude,
      longitude: fj.longitude,
      signalState: fj.signalState || 'green',
      preemptionStatus: fj.preemptionStatus || 'STANDBY',
    }));
  }, [usingSUMO, sumoJunctions, fallbackJunctions, bounds]);

  const junctionMap = useMemo(() => {
    const map = new Map<string, UnifiedJunction>();
    unifiedJunctions.forEach((j) => map.set(j.id, j));
    return map;
  }, [unifiedJunctions]);

  const unifiedRoads: UnifiedRoad[] = useMemo(() => {
    if (usingSUMO) {
      return sumoRoads.map((sr) => ({
        id: sr.id,
        fromJunction: sr.fromJunction,
        toJunction: sr.toJunction,
        lengthKm: (sr.lengthMeters || 1000) / 1000,
        trafficLevel: sr.trafficLevel || 'clear',
      }));
    }

    return fallbackRoads.map((fr) => ({
      id: fr.id,
      name: fr.name,
      fromJunction: fr.fromJunction || fr.fromJunctionId || '',
      toJunction: fr.toJunction || fr.toJunctionId || '',
      lengthKm: fr.lengthKm || fr.distanceKm || 1.2,
      trafficLevel: fr.trafficLevel || 'clear',
      geometry: fr.geometry,
    }));
  }, [usingSUMO, sumoRoads, fallbackRoads]);

  const liveTrafficMap = useMemo(() => {
    const map = new Map<string, TrafficDataItem>();
    liveTraffic.forEach((item) => {
      map.set(item.junctionId, item);
    });
    return map;
  }, [liveTraffic]);

  /*
   * ============================================================
   * ROUTE & PROGRESS
   * ============================================================
   */

  const ambulanceRoute = useMemo(() => {
    const route = activeVehicle.route?.pathJunctionIds;
    if (!Array.isArray(route)) return [];
    return route.filter((id): id is string => typeof id === 'string' && id.length > 0);
  }, [activeVehicle.route]);

  const rawProgress = Number(activeVehicle.progressPercent);
  const safeProgress = Number.isFinite(rawProgress)
    ? Math.max(0, Math.min(100, rawProgress))
    : 0;

  const routePoints: UnifiedJunction[] = useMemo(() => {
    if (ambulanceRoute.length === 0) return [];
    return ambulanceRoute
      .map((id) => junctionMap.get(id))
      .filter((j): j is UnifiedJunction => Boolean(j));
  }, [ambulanceRoute, junctionMap]);

  /*
   * ============================================================
   * GEOGRAPHIC & SCREEN POSITION INTERPOLATION ALONG ROAD PATH
   * ============================================================
   */

  const ambulancePosition = useMemo(() => {
    if (routePoints.length === 0) {
      return null;
    }

    if (routePoints.length === 1) {
      const p = routePoints[0];
      return { x: p.x, y: p.y, headingDeg: activeVehicle.headingDeg || 0 };
    }

    // At 0% progress: exactly at start junction
    if (safeProgress <= 0) {
      const start = routePoints[0];
      const next = routePoints[1];
      const heading =
        Math.atan2(next.y - start.y, next.x - start.x) * (180 / Math.PI);
      return { x: start.x, y: start.y, headingDeg: heading };
    }

    // At 100% progress: exactly at destination junction
    if (safeProgress >= 100) {
      const dest = routePoints[routePoints.length - 1];
      const prev = routePoints[routePoints.length - 2];
      const heading =
        Math.atan2(dest.y - prev.y, dest.x - prev.x) * (180 / Math.PI);
      return { x: dest.x, y: dest.y, headingDeg: heading };
    }

    // Calculate segment lengths along the route
    const segmentLengths: number[] = [];
    let totalLength = 0;

    for (let i = 0; i < routePoints.length - 1; i++) {
      const from = routePoints[i];
      const to = routePoints[i + 1];

      const road = unifiedRoads.find(
        (r) =>
          (r.fromJunction === from.id && r.toJunction === to.id) ||
          (r.fromJunction === to.id && r.toJunction === from.id)
      );

      const coordinateLength = Math.hypot(to.x - from.x, to.y - from.y);
      const segmentLength =
        road && Number.isFinite(road.lengthKm) && road.lengthKm > 0
          ? road.lengthKm * 10
          : Math.max(coordinateLength, 0.001);

      segmentLengths.push(segmentLength);
      totalLength += segmentLength;
    }

    if (totalLength <= 0) {
      const start = routePoints[0];
      return { x: start.x, y: start.y, headingDeg: 0 };
    }

    const travelled = (safeProgress / 100) * totalLength;
    let accumulated = 0;

    for (let i = 0; i < segmentLengths.length; i++) {
      const segmentLength = segmentLengths[i];
      const from = routePoints[i];
      const to = routePoints[i + 1];

      const segmentEnd = accumulated + segmentLength;

      if (travelled <= segmentEnd || i === segmentLengths.length - 1) {
        const localProgress =
          segmentLength > 0
            ? Math.max(0, Math.min(1, (travelled - accumulated) / segmentLength))
            : 0;

        const x = from.x + (to.x - from.x) * localProgress;
        const y = from.y + (to.y - from.y) * localProgress;
        const heading =
          Math.atan2(to.y - from.y, to.x - from.x) * (180 / Math.PI);

        return { x, y, headingDeg: heading };
      }

      accumulated += segmentLength;
    }

    const last = routePoints[routePoints.length - 1];
    return { x: last.x, y: last.y, headingDeg: 0 };
  }, [routePoints, safeProgress, unifiedRoads, activeVehicle.headingDeg]);

  /*
   * ============================================================
   * DISTANCE CALCULATION
   * ============================================================
   */

  const totalRouteDistance = Number(activeVehicle.route?.totalDistanceKm) || 3.2;

  const remainingDistance =
    !isNavigating && safeProgress === 0
      ? totalRouteDistance
      : safeProgress >= 100
      ? 0
      : Math.max(0, totalRouteDistance * (1 - safeProgress / 100));

  /*
   * ============================================================
   * GREEN CORRIDOR PATH
   * ============================================================
   */

  const greenCorridorPath = useMemo(() => {
    if (routePoints.length === 0) return '';
    return routePoints
      .map((junction, index) => `${index === 0 ? 'M' : 'L'} ${junction.x} ${junction.y}`)
      .join(' ');
  }, [routePoints]);

  /*
   * ============================================================
   * VEHICLE ICON
   * ============================================================
   */

  const VehicleIcon = () => {
    if (activeVehicle.type === 'ambulance') {
      return <Ambulance className="w-7 h-7" />;
    }
    if (activeVehicle.type === 'fireEngine') {
      return <Flame className="w-7 h-7" />;
    }
    return <Siren className="w-7 h-7" />;
  };

  /*
   * ============================================================
   * TRAFFIC SIGNAL ICON
   * ============================================================
   */

  const TrafficSignalIcon: React.FC<{ state: 'red' | 'yellow' | 'green' }> = ({
    state,
  }) => (
    <div className="relative w-6 h-9 rounded-md bg-slate-950 border border-white/70 shadow-xl flex flex-col items-center justify-center gap-[2px]">
      <div
        className={`w-1.5 h-1.5 rounded-full ${
          state === 'red'
            ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.9)]'
            : 'bg-red-950'
        }`}
      />
      <div
        className={`w-1.5 h-1.5 rounded-full ${
          state === 'yellow'
            ? 'bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.9)]'
            : 'bg-yellow-950'
        }`}
      />
      <div
        className={`w-1.5 h-1.5 rounded-full ${
          state === 'green'
            ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.9)]'
            : 'bg-green-950'
        }`}
      />
    </div>
  );

  return (
    <div className="relative w-full h-full overflow-hidden select-none bg-slate-900">
      {/* MAP BACKGROUND */}
      <div className="absolute inset-0 overflow-hidden bg-[#1e293b]">
        <div
          className="absolute inset-[-20%] opacity-40"
          style={{
            backgroundImage: `
              radial-gradient(ellipse at 25% 25%, rgba(30, 58, 138, 0.45) 0%, transparent 60%),
              radial-gradient(ellipse at 75% 75%, rgba(15, 118, 110, 0.35) 0%, transparent 60%),
              radial-gradient(ellipse at 50% 50%, rgba(51, 65, 85, 0.5) 0%, transparent 80%)
            `,
          }}
        />

        {/* Subtle grid pattern */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(255,255,255,0.08) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(255,255,255,0.08) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      {/* TOP HEADER BADGE */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
        <div className="px-3.5 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700/80 text-white text-[10px] font-black tracking-widest shadow-xl flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>RESQROUTE DYNAMIC EMERGENCY MAP</span>
        </div>
      </div>

      {/* MAP SVG CONTENT CANVAS */}
      <div
        className="absolute inset-0 transition-transform duration-300 origin-center"
        style={{ transform: `scale(${localZoom})` }}
      >
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          {/* ROADS */}
          {unifiedRoads.map((road) => {
            const from = junctionMap.get(road.fromJunction);
            const to = junctionMap.get(road.toJunction);
            if (!from || !to) return null;

            return (
              <g key={road.id}>
                {/* Outer casing */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#0f172a"
                  strokeWidth="4"
                  strokeLinecap="round"
                  opacity="0.9"
                />
                {/* Inner asphalt */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#334155"
                  strokeWidth="2.8"
                  strokeLinecap="round"
                />
                {/* Center divider line */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#64748b"
                  strokeWidth="0.8"
                  strokeDasharray="1.5 1.5"
                  strokeLinecap="round"
                  opacity="0.8"
                />

                {/* Traffic speed indicator */}
                {showTraffic && (
                  <line
                    x1={from.x}
                    y1={from.y}
                    x2={to.x}
                    y2={to.y}
                    stroke={
                      road.trafficLevel === 'heavy'
                        ? '#ef4444'
                        : road.trafficLevel === 'moderate'
                        ? '#f59e0b'
                        : '#38bdf8'
                    }
                    strokeWidth="0.6"
                    strokeDasharray="1 1"
                    strokeLinecap="round"
                    opacity="0.9"
                  />
                )}
              </g>
            );
          })}

          {/* GREEN CORRIDOR PATH */}
          {showGreenCorridor && greenCorridorPath && (
            <>
              {/* Outer pulsing glow */}
              <path
                d={greenCorridorPath}
                fill="none"
                stroke="#10b981"
                strokeWidth="5"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.4"
                className={isNavigating ? 'animate-pulse' : ''}
              />
              {/* Inner crisp corridor line */}
              <path
                d={greenCorridorPath}
                fill="none"
                stroke="#22c55e"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </>
          )}
        </svg>

        {/* JUNCTION MARKERS */}
        <div className="absolute inset-0 pointer-events-none">
          {unifiedJunctions.map((junction) => {
            const isRouteJunction = ambulanceRoute.includes(junction.id);
            const isStart = ambulanceRoute[0] === junction.id;
            const isDest = ambulanceRoute[ambulanceRoute.length - 1] === junction.id;

            return (
              <div
                key={junction.id}
                className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
                style={{ left: `${junction.x}%`, top: `${junction.y}%` }}
              >
                <div
                  className={`rounded-full border-2 shadow-lg flex items-center justify-center transition-all ${
                    isDest
                      ? 'w-6 h-6 bg-red-600 border-white text-white text-[9px] font-black ring-4 ring-red-500/30'
                      : isStart
                      ? 'w-5 h-5 bg-blue-600 border-white text-white text-[8px] font-black'
                      : isRouteJunction
                      ? 'w-4 h-4 bg-emerald-500 border-white text-white text-[7px] font-bold ring-2 ring-emerald-400/40'
                      : 'w-3 h-3 bg-slate-600 border-slate-300'
                  }`}
                >
                  {isRouteJunction ? junction.id.replace('J', '') : ''}
                </div>

                <div className="mt-0.5 px-1 py-0.2 rounded bg-slate-950/80 text-slate-300 text-[8px] font-bold whitespace-nowrap shadow">
                  {junction.id}
                </div>
              </div>
            );
          })}
        </div>

        {/* TRAFFIC SIGNALS */}
        {unifiedJunctions.map((junction) => {
          const isRouteJunction = ambulanceRoute.includes(junction.id);
          const live = liveTrafficMap.get(junction.id);

          const signalState: 'red' | 'yellow' | 'green' = isRouteJunction
            ? 'green' // Preempted for emergency vehicle
            : (live?.stateSummary || (junction.signalState as any) || 'green');

          return (
            <div
              key={`signal-${junction.id}`}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-20 pointer-events-none flex flex-col items-center"
              style={{
                left: `${junction.x + 2.5}%`,
                top: `${junction.y - 3.5}%`,
              }}
            >
              <TrafficSignalIcon state={signalState} />
            </div>
          );
        })}

        {/* DESTINATION HOSPITAL */}
        {hospitals.map((hospital) => {
          const isTarget =
            activeVehicle.selectedHospitalId === hospital.id ||
            activeVehicle.destinationJunctionId === hospital.junctionId ||
            activeVehicle.destinationName.toLowerCase().includes(hospital.name.toLowerCase()) ||
            hospital.name.toLowerCase().includes(activeVehicle.destinationName.toLowerCase());

          if (!isTarget) return null;

          const junction = hospital.junctionId
            ? junctionMap.get(hospital.junctionId)
            : undefined;

          const x = junction ? junction.x : hospital.x || 88;
          const y = junction ? junction.y : hospital.y || 52;

          return (
            <div
              key={hospital.id}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-30 pointer-events-none flex flex-col items-center"
              style={{ left: `${x}%`, top: `${y - 4}%` }}
            >
              <div className="absolute -inset-3 rounded-full bg-red-500/30 animate-ping" />
              <div className="relative w-10 h-10 rounded-full bg-red-600 border-2 border-white shadow-2xl flex items-center justify-center text-white">
                <Building2 className="w-5 h-5" />
              </div>
              <div className="mt-1 px-2.5 py-1 rounded-md bg-white text-slate-900 text-[10px] font-black shadow-xl whitespace-nowrap border border-slate-200">
                🏥 {hospital.name}
              </div>
            </div>
          );
        })}

        {/* 🚑 ACTIVE EMERGENCY VEHICLE */}
        {ambulancePosition && (
          <div
            className="absolute -translate-x-1/2 -translate-y-1/2 z-50 transition-all duration-[300ms] ease-linear"
            style={{
              left: `${ambulancePosition.x}%`,
              top: `${ambulancePosition.y}%`,
            }}
          >
            {/* Pulse ONLY while navigating */}
            {isNavigating && (
              <>
                <div className="absolute -inset-6 rounded-full border-2 border-red-500/40 animate-ping" />
                <div className="absolute -inset-3 rounded-full border-2 border-blue-400/60 animate-pulse" />
              </>
            )}

            <div
              className={`relative w-14 h-14 rounded-full flex items-center justify-center text-white border-[3px] border-white shadow-[0_0_25px_rgba(239,68,68,0.9)] transition-all ${
                activeVehicle.type === 'ambulance'
                  ? 'bg-red-600'
                  : activeVehicle.type === 'fireEngine'
                  ? 'bg-orange-500'
                  : 'bg-blue-600'
              }`}
            >
              <VehicleIcon />
            </div>

            <div
              className={`absolute -top-7 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full text-white text-[8px] font-black tracking-widest shadow-lg whitespace-nowrap ${
                safeProgress >= 100
                  ? 'bg-emerald-600'
                  : isNavigating
                  ? 'bg-red-600 animate-pulse'
                  : 'bg-blue-600'
              }`}
            >
              {safeProgress >= 100
                ? '✅ ARRIVED'
                : isNavigating
                ? '🚑 LIVE'
                : '🚑 READY'}
            </div>

            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 px-2 py-0.5 rounded-md bg-slate-950/95 text-white text-[9px] font-black whitespace-nowrap shadow-md border border-slate-700">
              {activeVehicle.id}
            </div>
          </div>
        )}
      </div>

      {/* TOP-LEFT STATUS HUD */}
      <div className="absolute top-4 left-4 z-40 pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur-md px-3.5 py-2.5 rounded-2xl shadow-2xl border border-slate-700/80 flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            {sumoLoading ? (
              <RefreshCw className="w-3.5 h-3.5 text-yellow-400 animate-spin" />
            ) : (
              <Radio
                className={`w-3.5 h-3.5 ${
                  usingSUMO ? 'text-emerald-400' : 'text-blue-400'
                }`}
              />
            )}
            <span className="text-[10px] font-black text-white uppercase tracking-wider">
              {sumoLoading
                ? 'Connecting Simulation'
                : usingSUMO
                ? `SUMO Live • ${sumoJunctions.length} Junctions`
                : `ResqRoute Mesh • ${unifiedJunctions.length} Junctions`}
            </span>
          </div>

          {/* Navigation status */}
          <div className="flex items-center justify-between gap-3 text-[9px] font-bold border-t border-slate-700/60 pt-1.5">
            <span className="text-slate-400 uppercase">State:</span>
            <span
              className={
                safeProgress >= 100
                  ? 'text-emerald-400 font-black'
                  : isNavigating
                  ? 'text-rose-400 font-black animate-pulse'
                  : 'text-yellow-400 font-black'
              }
            >
              {safeProgress >= 100
                ? 'ARRIVED (100%)'
                : isNavigating
                ? `NAVIGATING (${safeProgress.toFixed(0)}%)`
                : 'READY TO START'}
            </span>
          </div>

          <div className="flex items-center justify-between gap-3 text-[9px] font-bold">
            <span className="text-slate-400 uppercase">Distance Left:</span>
            <span className="text-white font-black">
              {remainingDistance.toFixed(1)} km
            </span>
          </div>
        </div>
      </div>

      {/* BOTTOM-RIGHT MAP ZOOM CONTROLS */}
      <div className="absolute right-4 bottom-4 z-40 flex flex-col bg-white/95 backdrop-blur rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        <button
          type="button"
          onClick={increaseZoom}
          className="w-10 h-10 flex items-center justify-center text-slate-700 hover:bg-slate-100 border-b border-slate-200 cursor-pointer transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={resetZoom}
          className="w-10 h-10 flex items-center justify-center text-blue-600 hover:bg-blue-50 border-b border-slate-200 cursor-pointer transition-colors"
          title="Reset View"
        >
          <LocateFixed className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={decreaseZoom}
          className="w-10 h-10 flex items-center justify-center text-slate-700 hover:bg-slate-100 cursor-pointer transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default GoogleMapView;