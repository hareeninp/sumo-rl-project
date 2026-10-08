import React from 'react';
import { EmergencyVehicle } from '../types';
import { Ambulance, Flame, Siren, Zap } from 'lucide-react';

interface ActiveEmergenciesPanelProps {
  vehicles: EmergencyVehicle[];
  selectedVehicleId: string;
  onSelectVehicle: (vehicleId: string) => void;
  onOpenPriorityFormula: () => void;
}

export const ActiveEmergenciesPanel: React.FC<ActiveEmergenciesPanelProps> = ({
  vehicles,
  selectedVehicleId,
  onSelectVehicle,
  onOpenPriorityFormula,
}) => {
  const getVehicleIcon = (type: EmergencyVehicle['type']) => {
    switch (type) {
      case 'ambulance':
        return Ambulance;
      case 'fireEngine':
        return Flame;
      case 'police':
        return Siren;
    }
  };

  return (
    <div className="w-full sm:w-80 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-slate-200 p-3 sm:p-4 text-slate-800 animate-in fade-in slide-in-from-left-4 duration-200">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
          <h4 className="text-xs font-black uppercase tracking-wider text-slate-900">
            Active Emergencies ({vehicles.length})
          </h4>
        </div>

        <button
          type="button"
          onClick={onOpenPriorityFormula}
          className="text-[10px] font-black uppercase tracking-wider text-blue-600 hover:text-blue-700 flex items-center gap-1 bg-blue-50 px-2 py-0.5 rounded-md"
          title="Open Dynamic Priority Score Matrix"
        >
          <Zap className="w-3 h-3 text-amber-500" />
          <span>Priority Matrix</span>
        </button>
      </div>

      <div className="space-y-2">
        {vehicles.map((v) => {
          const isSelected = v.id === selectedVehicleId;
          const Icon = getVehicleIcon(v.type);

          const statusBadge =
            v.priorityStatus === 'FAVOURED'
              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
              : v.priorityStatus === 'COORDINATING'
              ? 'bg-blue-100 text-blue-800 border-blue-300'
              : 'bg-slate-100 text-slate-700 border-slate-300';

          const priorityColor =
            v.priority === 'high'
              ? 'text-red-600'
              : v.priority === 'medium'
              ? 'text-amber-600'
              : 'text-emerald-600';

          return (
            <div
              key={v.id}
              onClick={() => onSelectVehicle(v.id)}
              className={`p-2.5 rounded-xl border-2 cursor-pointer transition-all flex items-center justify-between ${
                isSelected
                  ? 'border-blue-600 bg-blue-50/70 shadow-xs'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white ${
                    v.type === 'ambulance'
                      ? 'bg-red-600'
                      : v.type === 'fireEngine'
                      ? 'bg-orange-500'
                      : 'bg-blue-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-xs text-slate-900">{v.id}</span>
                    <span className={`text-[10px] font-black uppercase ${priorityColor}`}>
                      {v.priority.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 truncate max-w-[130px]">
                    {v.destinationName}
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0 flex flex-col items-end gap-0.5">
                <div className="text-xs font-black text-slate-900">
                  {Math.round(v.route?.etaMinutes || 6)} min
                </div>
                <div className={`text-[9px] font-black uppercase px-1.5 py-0.2 rounded border ${statusBadge}`}>
                  {v.priorityStatus}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
