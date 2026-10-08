import React from 'react';
import { EmergencyVehicle } from '../types';
import { routingService } from '../services/routingService';
import { Zap, X, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface PriorityScoreModalProps {
  vehicles: EmergencyVehicle[];
  onClose: () => void;
}

export const PriorityScoreModal: React.FC<PriorityScoreModalProps> = ({
  vehicles,
  onClose,
}) => {
  const conflictResult = routingService.resolveVehicleConflict(vehicles, 'J3');

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-2xl w-full shadow-2xl border border-slate-200 animate-in zoom-in-95 duration-150 my-8">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-100 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Zap className="w-6 h-6 fill-current" />
            </div>
            <div>
              <h3 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                DYNAMIC PRIORITY SCORE ENGINE
              </h3>
              <p className="text-xs text-slate-500 font-semibold">
                Multi-criteria green corridor arbitration algorithm
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Formula Box */}
        <div className="bg-slate-900 text-white p-4 rounded-2xl mb-6 font-mono text-xs shadow-inner">
          <div className="text-amber-400 font-bold mb-1 text-[11px] uppercase tracking-wider">
            Active Priority Formula (Section 26)
          </div>
          <div className="text-slate-200 leading-relaxed">
            Priority Score = (0.30 × Emergency Urgency) + (0.20 × ETA Urgency) + (0.20 × Junction Proximity) + (0.10 × Traffic Condition) + (0.10 × Route Conflict) + (0.10 × Accumulated Delay)
          </div>
          <div className="mt-2 text-[10px] text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Service Precedence (Fire &gt; Ambulance &gt; Police) used ONLY as final tie-breaker on equal scores.</span>
          </div>
        </div>

        {/* Contested Junction Status */}
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-2xl mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-amber-900 font-black text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Corridor Arbitration at Contested Node: Junction 3</span>
            </div>
            <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-amber-200 text-amber-900">
              Resolved
            </span>
          </div>

          <div className="text-xs text-amber-800 space-y-1">
            {conflictResult.explanation.map((exp, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                <span>{exp}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Breakdown of each vehicle */}
        <div className="space-y-4">
          <h4 className="text-xs font-black uppercase tracking-wider text-slate-500">
            Unit Factor Breakdown
          </h4>

          {vehicles.map((v) => {
            const breakdown = conflictResult.breakdowns[v.id] || routingService.calculateDynamicPriorityScore(v, 'J3', vehicles);
            const isWinner = v.id === conflictResult.favouredVehicleId;

            return (
              <div
                key={v.id}
                className={`p-4 rounded-2xl border-2 transition-all ${
                  isWinner
                    ? 'border-emerald-500 bg-emerald-50/40 shadow-sm'
                    : 'border-slate-200 bg-slate-50/60'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-black text-sm text-slate-900">{v.name} ({v.id})</span>
                    <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                      {v.type}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-lg font-black text-slate-900">
                      Score: {breakdown.totalScore}
                    </span>
                    <span
                      className={`text-xs font-black uppercase px-2.5 py-0.5 rounded-full ${
                        isWinner
                          ? 'bg-emerald-600 text-white shadow-xs'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {isWinner ? 'FAVOURED' : 'COORDINATING'}
                    </span>
                  </div>
                </div>

                {/* Factors grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] mb-3">
                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">Urgency (30%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.emergencyUrgency.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.emergencyUrgency.detail}</div>
                  </div>

                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">ETA Urgency (20%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.etaUrgency.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.etaUrgency.detail}</div>
                  </div>

                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">Proximity (20%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.junctionProximity.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.junctionProximity.detail}</div>
                  </div>

                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">Traffic (10%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.trafficCondition.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.trafficCondition.detail}</div>
                  </div>

                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">Conflict (10%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.routeConflict.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.routeConflict.detail}</div>
                  </div>

                  <div className="bg-white p-2 rounded-xl border border-slate-200">
                    <div className="text-slate-400 font-bold">Delay (10%)</div>
                    <div className="font-extrabold text-slate-800">{breakdown.factors.accumulatedDelay.score} pts</div>
                    <div className="text-[9px] text-slate-500 truncate">{breakdown.factors.accumulatedDelay.detail}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Close button */}
        <div className="mt-6 pt-4 border-t border-slate-100 text-right">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs uppercase tracking-wider hover:bg-slate-800 transition-colors"
          >
            Close Matrix
          </button>
        </div>
      </div>
    </div>
  );
};
