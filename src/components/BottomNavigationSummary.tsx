import React, { useState } from 'react';
import { VehicleType } from '../types';
import {
  Clock,
  Navigation,
  PhoneCall,
  Radio,
  Volume2,
  VolumeX,
  Type,
  Square,
  Play,
  Check,
  Compass,
  ExternalLink,
} from 'lucide-react';

interface BottomNavigationSummaryProps {
  vehicleType: VehicleType;
  vehicleId: string;
  etaMinutes: number;
  remainingDistanceKm: number;
  isNavigating: boolean;
  onToggleNavigation: () => void;
  isVoiceEnabled: boolean;
  onToggleVoice: () => void;
  isSimpleMode: boolean;
  onToggleSimpleMode: () => void;
  onOpenGoogleMaps?: () => void;
}

export const BottomNavigationSummary: React.FC<BottomNavigationSummaryProps> = ({
  vehicleType,
  vehicleId: _vehicleId,
  etaMinutes,
  remainingDistanceKm,
  isNavigating,
  onToggleNavigation,
  isVoiceEnabled,
  onToggleVoice,
  isSimpleMode,
  onToggleSimpleMode,
  onOpenGoogleMaps,
}) => {
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const handleActionClick = (actionName: string) => {
    setActionNotice(`Sent: ${actionName} protocol broadcast`);
    setTimeout(() => setActionNotice(null), 3000);
  };

  const getVehicleAction = () => {
    switch (vehicleType) {
      case 'ambulance':
        return {
          label: 'Call Hospital',
          icon: PhoneCall,
          color: 'bg-red-600 hover:bg-red-700 text-white',
        };
      case 'fireEngine':
        return {
          label: 'Dispatch Update',
          icon: Radio,
          color: 'bg-orange-600 hover:bg-orange-700 text-white',
        };
      case 'police':
        return {
          label: 'Report Status',
          icon: Radio,
          color: 'bg-blue-600 hover:bg-blue-700 text-white',
        };
    }
  };

  const action = getVehicleAction();

  const formattedEta =
    etaMinutes <= 0
      ? '0'
      : etaMinutes < 1
      ? '< 1'
      : String(Math.round(etaMinutes));

  const formattedDistance =
    remainingDistanceKm <= 0
      ? '0.0'
      : Number(remainingDistanceKm).toFixed(1);

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-11/12 max-w-2xl z-30 pointer-events-auto">
      {actionNotice && (
        <div className="mb-2 bg-emerald-600 text-white text-xs font-bold py-1.5 px-4 rounded-xl shadow-lg flex items-center justify-center gap-1.5 animate-in fade-in slide-in-from-bottom-2">
          <Check className="w-3.5 h-3.5" />
          <span>{actionNotice}</span>
        </div>
      )}

      <div className="bg-slate-900/95 backdrop-blur-md text-white rounded-2xl shadow-2xl border border-slate-700/80 p-3.5 sm:p-4 flex flex-wrap items-center justify-between gap-3">
        {/* Left: ETA & Remaining Distance */}
        <div className="flex items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400 leading-none">ETA</div>
              <div className="text-xl sm:text-2xl font-black text-white leading-tight">
                {formattedEta} <span className="text-xs font-bold text-slate-300">min</span>
              </div>
            </div>
          </div>

          <div className="h-8 w-px bg-slate-700/80" />

          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
              <Navigation className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400 leading-none">Remaining</div>
              <div className="text-xl sm:text-2xl font-black text-white leading-tight">
                {formattedDistance} <span className="text-xs font-bold text-slate-300">km</span>
              </div>
            </div>
          </div>
        </div>

        {/* Center/Right Buttons */}
        <div className="flex items-center gap-2 ml-auto flex-wrap">
          {/* Direct Google Maps Navigation Button */}
          {onOpenGoogleMaps && (
            <button
              type="button"
              onClick={onOpenGoogleMaps}
              className="px-3 py-2 rounded-xl text-xs font-black bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-md shadow-blue-600/30 border border-blue-400 flex items-center gap-1.5 transition-all hover:scale-105 cursor-pointer"
              title="Launch full navigation in Google Maps App or Web"
            >
              <Compass className="w-3.5 h-3.5 text-blue-200" />
              <span className="hidden xs:inline sm:inline">Google Maps</span>
              <ExternalLink className="w-3 h-3 text-blue-200" />
            </button>
          )}

          {/* Voice Toggle */}
          <button
            type="button"
            onClick={onToggleVoice}
            className={`p-2 rounded-xl border transition-all cursor-pointer ${
              isVoiceEnabled
                ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
            title="Voice guidance"
          >
            {isVoiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {/* Simple Mode Toggle */}
          <button
            type="button"
            onClick={onToggleSimpleMode}
            className={`px-3 py-2 rounded-xl text-xs font-bold border flex items-center gap-1.5 transition-all cursor-pointer ${
              isSimpleMode
                ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-500/30'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white'
            }`}
            title="Driver-safe simplified mode"
          >
            <Type className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Simple</span>
          </button>

          {/* One-Tap Action */}
          {!isSimpleMode && (
            <button
              type="button"
              onClick={() => handleActionClick(action.label)}
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold shadow-md transition-all cursor-pointer ${action.color}`}
            >
              <action.icon className="w-3.5 h-3.5" />
              <span>{action.label}</span>
            </button>
          )}

          {/* Start/End Navigation Button */}
          <button
            type="button"
            onClick={onToggleNavigation}
            className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-lg transition-all cursor-pointer ${
              isNavigating
                ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30 animate-pulse'
                : 'bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-black shadow-emerald-500/30'
            }`}
          >
            {isNavigating ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>END NAV</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>START NAV</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
