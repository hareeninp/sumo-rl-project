import React, { useState } from 'react';
import { MOCK_SCENARIOS } from '../data/mock/mockScenarios';
import { Scenario } from '../types';
import { PlaySquare, ChevronDown, ChevronUp, Check, AlertTriangle } from 'lucide-react';

interface ScenarioSelectorProps {
  currentScenarioId: string;
  onSelectScenario: (scenario: Scenario) => void;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  currentScenarioId,
  onSelectScenario,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const active = MOCK_SCENARIOS.find((s) => s.id === currentScenarioId) || MOCK_SCENARIOS[0];

  return (
    <div className="relative pointer-events-auto">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="px-3.5 py-2 rounded-2xl bg-white/95 backdrop-blur-md shadow-xl border border-slate-200 text-slate-800 text-xs font-black uppercase tracking-wider flex items-center gap-2 hover:bg-slate-50 transition-all cursor-pointer"
        title="Switch Hackathon Demo Scenario"
      >
        <PlaySquare className="w-4 h-4 text-blue-600" />
        <span className="truncate max-w-[140px] sm:max-w-[200px]">{active.title.split('—')[1] || active.title}</span>
        {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="absolute bottom-full mb-2 left-0 w-72 sm:w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 p-2.5 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="text-[10px] font-black uppercase tracking-wider text-slate-400 px-2 py-1 mb-1">
            Hackathon Demo Scenarios
          </div>

          <div className="space-y-1 max-h-64 overflow-y-auto">
            {MOCK_SCENARIOS.map((sc) => {
              const isCurrent = sc.id === currentScenarioId;

              return (
                <button
                  key={sc.id}
                  type="button"
                  onClick={() => {
                    onSelectScenario(sc);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left p-2.5 rounded-xl text-xs transition-all flex items-start justify-between gap-2 cursor-pointer ${
                    isCurrent
                      ? 'bg-blue-50 border border-blue-200 text-blue-900 font-bold'
                      : 'hover:bg-slate-50 text-slate-700 font-medium'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-1.5 font-bold text-slate-900">
                      <span>{sc.title}</span>
                      {sc.hasConflict && (
                        <AlertTriangle className="w-3 h-3 text-amber-500" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5">
                      {sc.description}
                    </p>
                  </div>

                  {isCurrent && (
                    <Check className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
