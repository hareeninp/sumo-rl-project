import { GPSState, GPSAccuracyStatus } from '../types';
import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';

export interface RawGeolocationResult {
  lat: number;
  lng: number;
  accuracy: number;
  heading: number | null;
  speed: number | null;
}

class GeoService {
  private watchId: number | null = null;
  private lastKnownGPSState: GPSState = {
    lat: null,
    lng: null,
    accuracyMeters: null,
    headingDeg: null,
    speedKmh: null,
    status: 'UNAVAILABLE',
    isRealGps: false,
  };

  /**
   * Request user's real browser latitude and longitude
   */
  public async getCurrentPosition(): Promise<RawGeolocationResult> {
    return new Promise((resolve, reject) => {
      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        this.lastKnownGPSState.status = 'UNAVAILABLE';
        this.lastKnownGPSState.errorMessage = 'Geolocation API not supported in this environment.';
        return reject(new Error('Geolocation is not supported by your browser.'));
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          const accuracy = position.coords.accuracy;
          const heading = position.coords.heading;
          const speed = position.coords.speed ? position.coords.speed * 3.6 : null; // m/s to km/h

          const status: GPSAccuracyStatus = accuracy <= 15 ? 'STRONG' : accuracy <= 50 ? 'WEAK' : 'UNAVAILABLE';

          this.lastKnownGPSState = {
            lat,
            lng,
            accuracyMeters: Math.round(accuracy),
            headingDeg: heading !== null ? Math.round(heading) : 42,
            speedKmh: speed !== null ? Math.round(speed) : 38,
            status,
            isRealGps: true,
          };

          resolve({ lat, lng, accuracy, heading, speed });
        },
        (error) => {
          this.lastKnownGPSState.status = 'UNAVAILABLE';
          this.lastKnownGPSState.errorMessage = error.message;
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 1000,
        }
      );
    });
  }

  /**
   * Watch live GPS stream
   */
  public watchPosition(callback: (gpsState: GPSState) => void): void {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      this.lastKnownGPSState.status = 'UNAVAILABLE';
      callback(this.lastKnownGPSState);
      return;
    }

    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
    }

    this.watchId = navigator.geolocation.watchPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const accuracy = position.coords.accuracy;
        const heading = position.coords.heading;
        const speed = position.coords.speed ? position.coords.speed * 3.6 : 38;

        const status: GPSAccuracyStatus = accuracy <= 15 ? 'STRONG' : accuracy <= 50 ? 'WEAK' : 'UNAVAILABLE';

        const updated: GPSState = {
          lat,
          lng,
          accuracyMeters: Math.round(accuracy),
          headingDeg: heading !== null ? Math.round(heading) : 42,
          speedKmh: Math.round(speed || 38),
          status,
          isRealGps: true,
        };

        this.lastKnownGPSState = updated;
        callback(updated);
      },
      (error) => {
        this.lastKnownGPSState = {
          ...this.lastKnownGPSState,
          status: 'UNAVAILABLE',
          errorMessage: error.message,
        };
        callback(this.lastKnownGPSState);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  }

  /**
   * Stop watching GPS
   */
  public stopWatching(): void {
    if (this.watchId !== null && typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  /**
   * Find nearest junction for a given real coordinate
   */
  public convertCoordsToMapPosition(lat: number, lng: number): { nearestJunctionId: string; distanceMeters: number } {
    let nearestId = MOCK_JUNCTIONS[0].id;
    let minDistance = Infinity;

    for (const junc of MOCK_JUNCTIONS) {
      // Euclidean approximation for distance calculation
      const dLat = (lat - junc.latitude) * 111320;
      const dLng = (lng - junc.longitude) * 111320 * Math.cos((lat * Math.PI) / 180);
      const dist = Math.sqrt(dLat * dLat + dLng * dLng);

      if (dist < minDistance) {
        minDistance = dist;
        nearestId = junc.id;
      }
    }

    return {
      nearestJunctionId: nearestId,
      distanceMeters: Math.round(minDistance),
    };
  }

  /**
   * Reverse geocode stub for human-readable address from lat/lng
   */
  public reverseGeocodeStub(lat: number, lng: number): string {
    const { nearestJunctionId } = this.convertCoordsToMapPosition(lat, lng);
    const junc = MOCK_JUNCTIONS.find((j) => j.id === nearestJunctionId);
    return `Live GPS (${lat.toFixed(4)}, ${lng.toFixed(4)}) - Near ${junc?.name || nearestJunctionId}`;
  }

  public getLastKnownGPS(): GPSState {
    return this.lastKnownGPSState;
  }
}

export const geoService = new GeoService();
