import React from 'react';
import {
  Shield,
  ArrowRight,
  Activity,
  Cpu,
  Radio,
  Siren,
  CheckCircle,
  Car,
} from 'lucide-react';

interface OpeningPageProps {
  onGetStarted: () => void;
  onQuickLogin: () => void;
  hasSavedSession: boolean;
  savedVehicleId?: string;
}

export const OpeningPage: React.FC<OpeningPageProps> = ({
  onGetStarted,
  onQuickLogin,
  hasSavedSession,
  savedVehicleId,
}) => {
  return (
    <div className="min-h-screen bg-linear-to-b from-sky-50 via-blue-50/60 to-white flex flex-col items-center justify-center p-4 sm:p-6 text-slate-800">

      {/* Top feature tags */}
      <div className="w-full max-w-4xl flex flex-wrap justify-center items-center gap-2 sm:gap-4 mb-8">

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-blue-100 shadow-xs text-xs font-semibold text-blue-800">
          <Activity className="w-3.5 h-3.5 text-blue-600" />
          <span>Smart Routing</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-blue-100 shadow-xs text-xs font-semibold text-blue-800">
          <Car className="w-3.5 h-3.5 text-blue-600" />
          <span>Real-time Traffic</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-emerald-100 shadow-xs text-xs font-semibold text-emerald-800">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
          <span>Green Corridor</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-indigo-100 shadow-xs text-xs font-semibold text-indigo-800">
          <Cpu className="w-3.5 h-3.5 text-indigo-600" />
          <span>Priority Handling</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-rose-100 shadow-xs text-xs font-semibold text-rose-800">
          <Siren className="w-3.5 h-3.5 text-rose-600" />
          <span>Multi Vehicle Support</span>
        </div>

      </div>


      {/* Main Card */}
      <div className="w-full max-w-md bg-white rounded-3xl p-8 sm:p-10 shadow-xl shadow-blue-500/10 border border-blue-100/80 flex flex-col items-center text-center relative overflow-hidden">

        {/* Subtle background glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-400/10 rounded-full blur-2xl pointer-events-none" />

        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-sky-400/10 rounded-full blur-2xl pointer-events-none" />


        {/* Heartbeat / Compass Icon */}
        <div className="relative mb-6">

          <div className="w-24 h-24 rounded-3xl bg-linear-to-tr from-blue-600 to-sky-500 flex items-center justify-center text-white shadow-xl shadow-blue-500/30 transform hover:scale-105 transition-transform duration-300">
            <Shield className="w-12 h-12 stroke-[1.8]" />
          </div>

          <div className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center border-2 border-white shadow-md">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>

        </div>


        {/* Brand Name */}
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mb-1">
          ResQ<span className="text-blue-600">Route</span>
        </h1>

        <p className="text-xs uppercase tracking-widest font-bold text-blue-600 mb-3">
          Smart Emergency Routing & Green Corridor
        </p>


        {/* Tagline */}
        <p className="text-slate-600 font-medium text-sm sm:text-base leading-relaxed mb-8 max-w-xs">
          Faster Routes. Smarter Signals. Safer Lives.
        </p>


        {/* Actions */}
        <div className="w-full space-y-3">

          <button
            onClick={onGetStarted}
            className="w-full py-4 px-6 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25 transition-all cursor-pointer"
          >
            <span>Get Started</span>
            <ArrowRight className="w-5 h-5" />
          </button>


          {hasSavedSession ? (

            <button
              onClick={onQuickLogin}
              className="w-full py-3.5 px-6 rounded-2xl bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-sm border border-slate-200 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>
                Resume as {savedVehicleId || 'Active Unit'}
              </span>

              <ArrowRight className="w-4 h-4 text-slate-500" />
            </button>

          ) : (

            <button
              onClick={onGetStarted}
              className="w-full py-3.5 px-6 rounded-2xl bg-white hover:bg-slate-50 text-slate-600 font-semibold text-sm border border-slate-200/80 transition-all cursor-pointer"
            >
              Sign In Unit
            </button>

          )}

        </div>


        {/* Footer trust badge */}
        <div className="mt-8 pt-6 border-t border-slate-100 w-full flex items-center justify-center gap-2 text-xs text-slate-400 font-medium">
          <span>
            SUMO Traffic & Green Corridor System
          </span>
        </div>

      </div>

    </div>
  );
};