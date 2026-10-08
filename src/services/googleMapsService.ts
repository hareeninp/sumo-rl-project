import { Junction, RouteOption } from '../types';
import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';

export interface GoogleMapsRouteParams {
  originLat: number;
  originLng: number;
  destLat: number;
  destLng: number;
  destinationName?: string;
  waypoints?: Array<{ lat: number; lng: number }>;
}

class GoogleMapsService {
  /**
   * Generates a Google Maps Universal URL to navigate directly
   * Doc: https://developers.google.com/maps/documentation/urls/get-started?utm_campaign=gmp_mcp_codeassist_v1_aistudio
   */
  public generateNavigationUrl(params: GoogleMapsRouteParams): string {
    const origin = `${params.originLat.toFixed(6)},${params.originLng.toFixed(6)}`;
    const destination = params.destinationName
      ? encodeURIComponent(`${params.destinationName} (${params.destLat.toFixed(6)}, ${params.destLng.toFixed(6)})`)
      : `${params.destLat.toFixed(6)},${params.destLng.toFixed(6)}`;

    let url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving&dir_action=navigate`;

    if (params.waypoints && params.waypoints.length > 0) {
      const waypointsParam = params.waypoints
        .map((wp) => `${wp.lat.toFixed(6)},${wp.lng.toFixed(6)}`)
        .join('|');
      url += `&waypoints=${encodeURIComponent(waypointsParam)}`;
    }

    return url;
  }

  /**
   * Generates Google Maps navigation URL from RouteOption & Junctions
   */
  public getUrlFromRoute(route: RouteOption, userGps?: { lat: number; lng: number } | null): string {
    const junctionMap = new Map<string, Junction>();
    MOCK_JUNCTIONS.forEach((j) => junctionMap.set(j.id, j));

    const pathJunctions = (route.pathJunctionIds || [])
      .map((id) => junctionMap.get(id))
      .filter(Boolean) as Junction[];

    if (pathJunctions.length === 0) {
      return 'https://www.google.com/maps';
    }

    const firstJunc = pathJunctions[0];
    const lastJunc = pathJunctions[pathJunctions.length - 1];

    const originLat = userGps?.lat ?? firstJunc.latitude;
    const originLng = userGps?.lng ?? firstJunc.longitude;

    const destLat = lastJunc.latitude;
    const destLng = lastJunc.longitude;

    // Intermediate waypoints for green corridor path
    const intermediateWaypoints = pathJunctions.slice(1, -1).map((j) => ({
      lat: j.latitude,
      lng: j.longitude,
    }));

    return this.generateNavigationUrl({
      originLat,
      originLng,
      destLat,
      destLng,
      destinationName: lastJunc.name,
      waypoints: intermediateWaypoints.length > 0 ? intermediateWaypoints : undefined,
    });
  }

  /**
   * Launch navigation in Google Maps
   */
  public launchGoogleMaps(route: RouteOption, userGps?: { lat: number; lng: number } | null): void {
    const url = this.getUrlFromRoute(route, userGps);
    if (typeof window !== 'undefined') {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }
}

export const googleMapsService = new GoogleMapsService();
