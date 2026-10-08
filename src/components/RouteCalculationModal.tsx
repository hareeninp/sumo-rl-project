import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Loader2,
  ShieldAlert,
  ArrowLeft,
} from 'lucide-react';

interface RouteCalculationModalProps {
  onComplete: () => void;
  onCancel?: () => void;
}

const STEPS = [
  'Reading emergency priority & clinical status',
  'Interfacing with live traffic feed',
  'Analyzing weather conditions & wet pavement',
  'Checking active road construction on bypasses',
  'Evaluating multi-arterial path candidates',
  'Calculating Dynamic Priority Score & weights',
  'Checking contested junction conflicts (J3/J6)',
  'Synchronizing Green Corridor signal preemption',
];

export const RouteCalculationModal: React.FC<
  RouteCalculationModalProps
> = ({ onComplete, onCancel }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < STEPS.length - 1) {
          return prev + 1;
        }

        window.clearInterval(interval);

        window.setTimeout(() => {
          onComplete();
        }, 150);

        return prev;
      });
    }, 150);

    return () => {
      window.clearInterval(interval);
    };
  }, [onComplete]);

  const progress = ((currentStepIndex + 1) / STEPS.length) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-md">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl sm:p-8">
        
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-lg">
              <Activity className="h-6 w-6 animate-pulse" />
            </div>

            <div>
              <h3 className="text-xl font-black tracking-tight text-slate-900">
                CALCULATING BEST ROUTE
              </h3>

              <p className="text-xs font-semibold text-slate-500">
                Dynamic multi-factor optimization in progress...
              </p>
            </div>
          </div>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="cursor-pointer rounded-xl bg-slate-100 p-2 text-slate-600 transition-colors hover:bg-slate-200"
              title="Cancel and go back to Emergency Form"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Calculation steps */}
        <div className="my-6 space-y-2.5">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;

            return (
              <div
                key={idx}
                className={`flex items-center gap-3 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all ${
                  isDone
                    ? 'bg-emerald-50/70 text-emerald-700'
                    : isCurrent
                    ? 'border border-blue-200 bg-blue-50 text-blue-700'
                    : 'text-slate-400 opacity-60'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                ) : isCurrent ? (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-blue-600" />
                ) : (
                  <div className="h-4 w-4 shrink-0 rounded-full border border-slate-300" />
                )}

                <span className="truncate">{step}</span>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-600 to-emerald-500 transition-all duration-150"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Status */}
        <div className="mt-4 flex items-center justify-between text-[11px] font-bold text-slate-500">
          <span className="flex items-center gap-1">
            <ShieldAlert className="h-3.5 w-3.5 text-blue-500" />
            <span>Green Corridor Protocol</span>
          </span>

          <span>{Math.round(progress)}%</span>
        </div>

        {/* Cancel */}
        {onCancel && (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-slate-100 px-4 py-2.5 text-xs font-bold text-slate-700 transition-colors hover:bg-slate-200"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Cancel & Return to Emergency Form</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};