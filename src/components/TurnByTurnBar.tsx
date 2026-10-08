import React from 'react';
import { TurnInstruction } from '../types';
import {
  ArrowUp,
  CornerUpRight,
  CornerUpLeft,
  ArrowUpRight,
  ArrowUpLeft,
  CheckCircle2,
  Volume2,
  VolumeX,
  ArrowLeft,
  Compass,
  ExternalLink,
} from 'lucide-react';

interface TurnByTurnBarProps {
  instruction: TurnInstruction;
  isVoiceEnabled: boolean;
  onToggleVoice: () => void;
  isRecalculating?: boolean;
  onBack?: () => void;
  onOpenGoogleMaps?: () => void;
}

export const TurnByTurnBar: React.FC<TurnByTurnBarProps> = ({
  instruction,
  isVoiceEnabled,
  onToggleVoice,
  isRecalculating,
  onBack,
  onOpenGoogleMaps,
}) => {
  const getManeuverIcon = (maneuver: TurnInstruction['maneuver']) => {
    switch (maneuver) {
      case 'turn_right':
        return CornerUpRight;
      case 'turn_left':
        return CornerUpLeft;
      case 'slight_right':
        return ArrowUpRight;
      case 'slight_left':
        return ArrowUpLeft;
      case 'arrive':
        return CheckCircle2;
      case 'straight':
      default:
        return ArrowUp;
    }
  };

  const ManeuverIcon = getManeuverIcon(instruction.maneuver);

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 w-11/12 max-w-2xl z-30 pointer-events-auto">
      <div className="bg-slate-900/95 backdrop-blur-md text-white rounded-2xl shadow-2xl border border-slate-700/80 p-3 sm:p-4 flex items-center justify-between gap-3 sm:gap-4">
        {isRecalculating ? (
          <div className="flex items-center gap-3 w-full py-1">
            <div className="w-8 h-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
            <div>
              <div className="text-sm font-extrabold text-amber-400 uppercase tracking-wider animate-pulse">
                RECALCULATING ROUTE...
              </div>
              <p className="text-xs text-slate-300 font-medium">Resolving best unobstructed corridor</p>
            </div>
          </div>
        ) : (
          <>
            {/* Back Button to Emergency Form */}
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="w-10 h-10 rounded-xl bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-300 hover:text-white flex items-center justify-center shrink-0 border border-slate-700 transition-colors cursor-pointer"
                title="Go back to Emergency Form"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}

            {/* Left Maneuver Icon */}
            <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/30">
              <ManeuverIcon className="w-7 h-7 sm:w-8 sm:h-8 stroke-[2.5]" />
            </div>

            {/* Instruction Text & Distance */}
            <div className="grow min-w-0">
              <div className="text-xl sm:text-3xl font-black tracking-tight text-white leading-none mb-1 flex items-baseline gap-1.5 sm:gap-2">
                <span>{instruction.distanceMeters}</span>
                <span className="text-sm sm:text-lg font-bold text-emerald-400">m</span>
              </div>
              <div className="text-xs sm:text-base font-bold text-slate-100 truncate">
                {instruction.instruction}
              </div>
              <div className="text-[10px] sm:text-[11px] text-slate-400 font-medium truncate">
                Upcoming: {instruction.roadName} ({instruction.junctionId})
              </div>
            </div>

            {/* Actions group */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Direct Google Maps Navigation button */}
              {onOpenGoogleMaps && (
                <button
                  type="button"
                  onClick={onOpenGoogleMaps}
                  className="px-3 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-blue-500/30 border border-blue-400 transition-all hover:scale-105 cursor-pointer"
                  title="Open live turn-by-turn navigation in Google Maps"
                >
                  <Compass className="w-4 h-4 text-blue-200" />
                  <span className="hidden sm:inline">Google Maps</span>
                  <ExternalLink className="w-3 h-3 text-blue-200" />
                </button>
              )}

              {/* Voice Guidance Toggle */}
              <button
                type="button"
                onClick={onToggleVoice}
                className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all cursor-pointer ${
                  isVoiceEnabled
                    ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/30'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
                title={isVoiceEnabled ? 'Mute Voice Guidance' : 'Enable Voice Guidance'}
              >
                {isVoiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

