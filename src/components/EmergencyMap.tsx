import React from 'react';

import {
  EmergencyVehicle,
  NormalVehicle,
  Hospital,
  Junction,
  Road,
  WeatherData,
} from '../types';

import { GoogleMapView } from './GoogleMapView';

interface EmergencyMapProps {
  junctions: Junction[];
  roads: Road[];
  hospitals: Hospital[];
  emergencyVehicles: EmergencyVehicle[];
  normalVehicles: NormalVehicle[];
  sumoVehicles?: any[];
  trafficData?: any[];
  activeVehicleId: string;
  onSelectVehicle: (vehicleId: string) => void;
  showTraffic: boolean;
  showGreenCorridor: boolean;
  weather: WeatherData;
  zoomLevel: number;
  isNavigating: boolean;
  isSimpleMode: boolean;
}

export const EmergencyMap: React.FC<EmergencyMapProps> = ({
  junctions,
  roads,
  hospitals,
  emergencyVehicles,
  sumoVehicles = [],
  trafficData = [],
  activeVehicleId,
  showTraffic,
  showGreenCorridor,
  weather,
  zoomLevel,
  isNavigating,
  isSimpleMode,
}) => {
  const activeVehicle =
    emergencyVehicles.find(
      (vehicle) => vehicle.id === activeVehicleId
    ) || emergencyVehicles[0];

  if (!activeVehicle) {
    return null;
  }

  return (
    <div className="relative w-full h-full overflow-hidden">

      <GoogleMapView
        junctions={junctions}
        roads={roads}
        hospitals={hospitals}
        activeVehicle={activeVehicle}
        sumoVehicles={sumoVehicles}
        trafficData={trafficData}
        showTraffic={showTraffic}
        showGreenCorridor={showGreenCorridor}
        weather={weather}
        zoomLevel={zoomLevel}
        isNavigating={isNavigating}
        isSimpleMode={isSimpleMode}
      />

      <div className="absolute left-5 top-1/2 -translate-y-1/2 z-50 flex flex-col">

        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">

          <button
            type="button"
            title="Zoom in"
            className="w-12 h-12 flex items-center justify-center text-2xl font-bold text-slate-700 bg-white hover:bg-slate-50 border-b border-slate-200"
            onClick={() => {
              window.dispatchEvent(
                new CustomEvent('resqroute-zoom-in')
              );
            }}
          >
            +
          </button>

          <button
            type="button"
            title="Zoom out"
            className="w-12 h-12 flex items-center justify-center text-2xl font-bold text-slate-700 bg-white hover:bg-slate-50"
            onClick={() => {
              window.dispatchEvent(
                new CustomEvent('resqroute-zoom-out')
              );
            }}
          >
            −
          </button>

        </div>

      </div>

    </div>
  );
};