import React from 'react';
import {
  Crosshair,
  Layers,
  Sparkles,
  ArrowLeft,
} from 'lucide-react';

interface MapControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRecenter: () => void;
  showTraffic: boolean;
  onToggleTraffic: () => void;
  showGreenCorridor: boolean;
  onToggleGreenCorridor: () => void;
  onNewEmergency: () => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  onZoomIn: _onZoomIn,
  onZoomOut: _onZoomOut,
  onRecenter,
  showTraffic,
  onToggleTraffic,
  showGreenCorridor,
  onToggleGreenCorridor,
  onNewEmergency,
}) => {
  return (
    <div className="flex flex-col gap-2 pointer-events-auto">

      {/* =====================================================
          MAP ACTIONS
          Zoom controls are intentionally removed.
          EmergencyMap.tsx owns the zoom controls.
      ===================================================== */}

      <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-slate-200 p-1 flex flex-col items-center gap-1">

        {/* Recenter */}
        <button
          type="button"
          onClick={onRecenter}
          className="
            w-10
            h-10
            rounded-xl
            hover:bg-slate-100
            text-blue-600
            flex
            items-center
            justify-center
            transition-colors
            cursor-pointer
          "
          title="Recenter Active Emergency Vehicle"
        >
          <Crosshair className="w-5 h-5" />
        </button>

      </div>


      {/* =====================================================
          LAYER TOGGLES
      ===================================================== */}

      <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-slate-200 p-1 flex flex-col items-center gap-1">

        {/* Traffic */}
        <button
          type="button"
          onClick={onToggleTraffic}
          className={`
            w-10
            h-10
            rounded-xl
            flex
            items-center
            justify-center
            transition-colors
            cursor-pointer
            ${
              showTraffic
                ? 'bg-amber-100 text-amber-800'
                : 'hover:bg-slate-100 text-slate-400'
            }
          `}
          title="Toggle Live Traffic Congestion Overlays"
        >
          <Layers className="w-5 h-5" />
        </button>


        {/* Green Corridor */}
        <button
          type="button"
          onClick={onToggleGreenCorridor}
          className={`
            w-10
            h-10
            rounded-xl
            flex
            items-center
            justify-center
            transition-colors
            cursor-pointer
            ${
              showGreenCorridor
                ? 'bg-emerald-100 text-emerald-800'
                : 'hover:bg-slate-100 text-slate-400'
            }
          `}
          title="Toggle Dynamic Green Corridor Glow"
        >
          <Sparkles className="w-5 h-5" />
        </button>

      </div>


      {/* =====================================================
          BACK TO EMERGENCY FORM
      ===================================================== */}

      <button
        type="button"
        onClick={onNewEmergency}
        className="
          px-3.5
          py-2.5
          rounded-2xl
          bg-white/95
          hover:bg-white
          text-slate-800
          font-extrabold
          text-xs
          shadow-xl
          border
          border-slate-200
          flex
          items-center
          gap-2
          transition-all
          hover:scale-105
          cursor-pointer
        "
        title="Return to emergency form / Go to previous page"
      >
        <ArrowLeft className="w-4 h-4 text-blue-600" />

        <span>
          ← Back to Form
        </span>

      </button>

    </div>
  );
};