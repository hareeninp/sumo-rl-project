import React from 'react';
import { Radio, Cpu, Network } from 'lucide-react';
import { GPSAccuracyStatus } from '../types';

interface SystemStatusProps {
  gpsStatus: GPSAccuracyStatus;
  scenarioTitle?: string;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({
  gpsStatus,
  scenarioTitle,
}) => {
  return (
    <div className="bg-slate-900/90 backdrop-blur-md text-white rounded-2xl shadow-xl border border-slate-700/80 px-3.5 py-2 flex flex-wrap items-center gap-3 text-xs font-semibold pointer-events-auto">
      {/* Demo status */}
      <div className="flex items-center gap-1.5 text-emerald-400">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="font-extrabold uppercase tracking-wider text-[10px]">
          {scenarioTitle ? 'SIMULATION MODE' : 'DEMO MODE'}
        </span>
      </div>

      <div className="h-3 w-px bg-slate-700 hidden sm:block" />

      {/* GPS Indicator (Section 77) */}
      <div className="flex items-center gap-1.5">
        <Radio
          className={`w-3.5 h-3.5 ${
            gpsStatus === 'STRONG'
              ? 'text-emerald-400'
              : gpsStatus === 'WEAK'
              ? 'text-amber-400'
              : 'text-rose-400'
          }`}
        />
        <span className="text-[11px] text-slate-300">
          GPS:{' '}
          <strong
            className={
              gpsStatus === 'STRONG'
                ? 'text-emerald-400'
                : gpsStatus === 'WEAK'
                ? 'text-amber-400'
                : 'text-rose-400'
            }
          >
            {gpsStatus}
          </strong>
        </span>
      </div>

      <div className="h-3 w-px bg-slate-700 hidden md:block" />

      {/* Simulation / Traffic Signal Engine bridge */}
      <div className="hidden md:flex items-center gap-2 text-[10px] text-slate-400">
        <span className="flex items-center gap-1">
          <Network className="w-3 h-3 text-blue-400" />
          <span>Traffic Engine (SUMO/TraCI)</span>
        </span>
        <span>•</span>
        <span className="flex items-center gap-1">
          <Cpu className="w-3 h-3 text-emerald-400" />
          <span>Signal Control Network</span>
        </span>
      </div>
    </div>
  );
};
