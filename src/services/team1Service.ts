import {
  Junction,
  Road,
  NormalVehicle,
  WeatherData,
} from '../types';

import { MOCK_NORMAL_VEHICLES } from '../data/mock/mockVehicles';
import {
  MOCK_WEATHER,
  MOCK_ROAD_CONDITIONS,
} from '../data/mock/mockConditions';

const API_BASE_URL = 'http://127.0.0.1:5000';

export const team1Service = {

  // ============================================================
  // SUMO NETWORK
  // ============================================================

  async getNetwork(): Promise<{
    junctions: Junction[];
    roads: Road[];
  }> {

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/network`
      );

      if (!response.ok) {
        throw new Error(
          'SUMO network API request failed'
        );
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(
          result.error || 'SUMO network error'
        );
      }

      // --------------------------------------------------------
      // Find coordinate boundaries
      // --------------------------------------------------------

      const rawJunctions = result.junctions || [];

      if (rawJunctions.length === 0) {
        return {
          junctions: [],
          roads: [],
        };
      }

      const xs = rawJunctions.map(
        (j: any) => Number(j.x)
      );

      const ys = rawJunctions.map(
        (j: any) => Number(j.y)
      );

      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);

      const width =
        maxX - minX || 1;

      const height =
        maxY - minY || 1;

      // --------------------------------------------------------
      // Convert SUMO coordinates to 0-100 map coordinates
      // --------------------------------------------------------

      const junctions: Junction[] =
        rawJunctions.map(
          (j: any) => {

            const x =
              ((Number(j.x) - minX) /
                width) *
              90 +
              5;

            // SVG Y axis goes downward,
            // SUMO coordinates go upward.
            const y =
              95 -
              ((Number(j.y) - minY) /
                height) *
                90;

            return {
              id: j.id,
              name: j.id,

              x,
              y,

              latitude: 0,
              longitude: 0,

              signalState: 'red',

              preemptionStatus:
                'STANDBY',

              connectedJunctions: [],
            };
          }
        );

      // --------------------------------------------------------
      // Build junction lookup
      // --------------------------------------------------------

      const junctionMap =
        new Map<string, Junction>();

      junctions.forEach((j) => {
        junctionMap.set(j.id, j);
      });

      // --------------------------------------------------------
      // Convert SUMO roads
      // --------------------------------------------------------

      const roads: Road[] =
        (result.roads || [])
          .map((r: any) => {

            const from =
              junctionMap.get(
                r.fromJunction
              );

            const to =
              junctionMap.get(
                r.toJunction
              );

            if (!from || !to) {
              return null;
            }

            const speedKmh =
              Number(r.speedLimitMs || 0) *
              3.6;

            return {
              id: r.id,

              name: r.id,

              fromJunction:
                r.fromJunction,

              toJunction:
                r.toJunction,

              lengthKm:
                Number(
                  r.lengthMeters || 0
                ) / 1000,

              speedLimitKmh:
                speedKmh,

              lanes:
                Number(
                  r.laneCount || 1
                ),

              trafficLevel:
                'clear',

              averageSpeedKmh:
                speedKmh,

              condition:
                'normal',

              conditionDetails:
                undefined,

              weatherImpact:
                undefined,
            } as Road;
          })
          .filter(
            Boolean
          ) as Road[];

      // --------------------------------------------------------
      // Build connected junction information
      // --------------------------------------------------------

      roads.forEach((road) => {

        const from =
          junctionMap.get(
            road.fromJunction
          );

        if (
          from &&
          !from.connectedJunctions.includes(
            road.toJunction
          )
        ) {
          from.connectedJunctions.push(
            road.toJunction
          );
        }

      });

      return {
        junctions,
        roads,
      };

    } catch (error) {

      console.error(
        'Failed to fetch SUMO network:',
        error
      );

      return {
        junctions: [],
        roads: [],
      };
    }
  },


  // ============================================================
  // REAL-TIME SUMO TRAFFIC
  // ============================================================

  async getTrafficData() {

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/traffic`
      );

      if (!response.ok) {
        throw new Error(
          'Traffic API request failed'
        );
      }

      const result =
        await response.json();

      if (!result.success) {
        throw new Error(
          result.error ||
          'Traffic API error'
        );
      }

      return (result.data || []).map(
        (junction: any) => ({

          roadId:
            junction.junctionId,

          vehicleCount:
            junction.vehicleCount,

          averageSpeed:
            junction.averageSpeed,

          trafficLevel:
            junction.vehicleCount > 30
              ? 'heavy'
              : junction.vehicleCount > 15
              ? 'moderate'
              : 'light',

          travelTimeSec:
            0,

          queueLength:
            junction.queueLength,

          signalPhase:
            junction.signalPhase,
        })
      );

    } catch (error) {

      console.error(
        'Failed to fetch SUMO traffic data:',
        error
      );

      return [];
    }
  },


  // ============================================================
  // NORMAL VEHICLES
  // ============================================================

  getNormalVehicles():
    NormalVehicle[] {

    return MOCK_NORMAL_VEHICLES;
  },


  // ============================================================
  // WEATHER
  // ============================================================

  getWeatherData():
    WeatherData {

    return MOCK_WEATHER;
  },


  // ============================================================
  // ROAD CONDITIONS
  // ============================================================

  getRoadConditions() {

    return MOCK_ROAD_CONDITIONS;
  },


  // ============================================================
  // LANES
  // ============================================================

  getLanes() {

    return [];
  },
};