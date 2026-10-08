import React from 'react';
import { CheckCircle2, ArrowLeft, Clock, Navigation, Award, ShieldCheck, Compass, ExternalLink } from 'lucide-react';
import { EmergencyVehicle } from '../types';
import { googleMapsService } from '../services/googleMapsService';

interface ArrivalModalProps {
  vehicle: EmergencyVehicle;
  onNewEmergency: () => void;
  onOpenGoogleMaps?: () => void;
}

export const ArrivalModal: React.FC<ArrivalModalProps> = ({ vehicle, onNewEmergency, onOpenGoogleMaps }) => {
  const handleGoogleMaps = () => {
    if (onOpenGoogleMaps) {
      onOpenGoogleMaps();
    } else if (vehicle.route) {
      googleMapsService.launchGoogleMaps(vehicle.route);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-emerald-100 text-center animate-in zoom-in-95 duration-200">
        {/* Arrival Badge */}
        <div className="w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/20">
          <CheckCircle2 className="w-12 h-12" />
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-black uppercase tracking-wider mb-2">
          <Award className="w-3.5 h-3.5 text-emerald-600" />
          <span>DESTINATION REACHED</span>
        </div>

        <h3 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mb-1">
          ✅ ARRIVED
        </h3>
        <p className="text-sm font-bold text-slate-700 mb-6">
          {vehicle.destinationName}
        </p>

        {/* Trip Stats */}
        <div className="grid grid-cols-2 gap-3 bg-slate-50 p-4 rounded-2xl border border-slate-200/80 mb-6">
          <div className="flex flex-col items-center">
            <div className="flex items-center gap-1 text-slate-400 text-xs font-bold uppercase mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Total Time</span>
            </div>
            <span className="text-2xl font-black text-slate-900">
              {Math.max(4, Math.round(vehicle.route?.etaMinutes || 6))} min
            </span>
          </div>

          <div className="flex flex-col items-center border-l border-slate-200">
            <div className="flex items-center gap-1 text-slate-400 text-xs font-bold uppercase mb-1">
              <Navigation className="w-3.5 h-3.5" />
              <span>Distance</span>
            </div>
            <span className="text-2xl font-black text-slate-900">
              {vehicle.route?.totalDistanceKm || 4.2} km
            </span>
          </div>
        </div>

        <div className="p-3 bg-emerald-50/70 rounded-xl border border-emerald-200/70 text-left text-xs text-emerald-900 font-medium mb-6 flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Green Corridor Successful</div>
            <div>All synchronized junctions recovered to standard civilian traffic cycles.</div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2.5">
          <button
            type="button"
            onClick={handleGoogleMaps}
            className="w-full py-3 px-6 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-md shadow-blue-500/30 transition-all cursor-pointer"
          >
            <Compass className="w-4 h-4 text-blue-200" />
            <span>OPEN IN GOOGLE MAPS</span>
            <ExternalLink className="w-3.5 h-3.5 text-blue-200" />
          </button>

          <button
            type="button"
            onClick={onNewEmergency}
            className="w-full py-3.5 px-6 rounded-2xl bg-slate-900 hover:bg-slate-800 active:scale-[0.98] text-white font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg transition-all cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>← NEW EMERGENCY</span>
          </button>
        </div>
      </div>
    </div>
  );
};

