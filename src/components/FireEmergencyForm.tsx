import React, { useState } from 'react';
import { User, PriorityLevel } from '../types';
import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';
import { geoService } from '../services/geoService';
import { Flame, ArrowRight, ArrowLeft, Radio, AlertCircle } from 'lucide-react';

interface FireEmergencyFormProps {
  user: User;
  onBack?: () => void;
  onSubmit: (data: {
    destinationName: string;
    destinationJunctionId: string;
    priority: PriorityLevel;
    startLocationJunctionId: string;
    isUsingLiveGps: boolean;
    liveGpsCoords?: { lat: number; lng: number };
  }) => void;
}

export const FireEmergencyForm: React.FC<FireEmergencyFormProps> = ({
  user,
  onBack,
  onSubmit,
}) => {
  const [destination, setDestination] = useState('South Industrial District - Factory 4');
  const [priority, setPriority] = useState<PriorityLevel>('high');
  const [startLocation, setStartLocation] = useState('J2');
  const [isLocating, setIsLocating] = useState(false);
  const [gpsFeedback, setGpsFeedback] = useState<string | null>(null);
  const [liveCoords, setLiveCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const handleUseCurrentLocation = async () => {
    setIsLocating(true);
    setGpsFeedback(null);
    try {
      const pos = await geoService.getCurrentPosition();
      const { nearestJunctionId, distanceMeters } = geoService.convertCoordsToMapPosition(
        pos.lat,
        pos.lng
      );
      setStartLocation(nearestJunctionId);
      setLiveCoords({ lat: pos.lat, lng: pos.lng });
      setGpsFeedback(
        `📍 Live GPS lock: ${pos.lat.toFixed(4)}, ${pos.lng.toFixed(4)} (±${Math.round(pos.accuracy)}m) → Snapped to ${nearestJunctionId} (~${distanceMeters}m away)`
      );
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unable to acquire GPS lock.';
      setGpsFeedback(`LOCATION UNAVAILABLE: ${errorMessage} Using manual starting location.`);
    } finally {
      setIsLocating(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs: string[] = [];
    if (!destination.trim()) errs.push('Please enter an emergency destination.');
    if (!priority) errs.push('Please select emergency priority.');
    if (!startLocation) errs.push('Please select a starting location.');

    if (errs.length > 0) {
      setErrors(errs);
      return;
    }

    setErrors([]);
    // Assign destination junction logically
    let destJunctionId = 'J11';
    const lower = destination.toLowerCase();
    if (lower.includes('waterfront') || lower.includes('pier') || lower.includes('dock')) destJunctionId = 'J8';
    else if (lower.includes('mall') || lower.includes('civic')) destJunctionId = 'J4';
    else if (lower.includes('tech') || lower.includes('park')) destJunctionId = 'J5';
    else if (lower.includes('cross') || lower.includes('junction 3')) destJunctionId = 'J3';

    onSubmit({
      destinationName: destination.trim(),
      destinationJunctionId: destJunctionId,
      priority,
      startLocationJunctionId: startLocation,
      isUsingLiveGps: !!liveCoords,
      liveGpsCoords: liveCoords || undefined,
    });
  };

  return (
    <div className="max-w-2xl mx-auto py-4 sm:py-8 px-4">
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xl shadow-slate-200/80 border border-slate-200/90">
        {/* Title Header */}
        <div className="flex items-center justify-between gap-3.5 mb-6 pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3.5">
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center justify-center transition-colors cursor-pointer shrink-0"
                title="Go back to vehicle selection"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <div className="w-12 h-12 rounded-2xl bg-orange-500 text-white flex items-center justify-center shadow-lg shadow-orange-500/25 shrink-0">
              <Flame className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900">
                  FIRE & RESCUE EMERGENCY
                </h2>
                <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-orange-100 text-orange-700">
                  {user.vehicleId}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 font-medium">
                Specify fire / incident destination to calculate clear turning-radius green corridors.
              </p>
            </div>
          </div>
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Change Unit</span>
            </button>
          )}
        </div>

        {errors.length > 0 && (
          <div className="mb-5 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl text-xs font-semibold space-y-1">
            {errors.map((err, i) => (
              <div key={i} className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500" />
                <span>{err}</span>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Destination Free Text Input */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Emergency Destination <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Industrial Area, City Mall, Building 4, Junction 3..."
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-100 text-slate-900 font-semibold text-sm outline-none transition-all"
            />
          </div>

          {/* Emergency Priority Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Emergency Severity <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setPriority('high')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'high'
                    ? 'border-red-600 bg-red-600 text-white shadow-lg shadow-red-600/30'
                    : 'border-slate-200 hover:border-red-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🔴 Critical</span>
                <span className={`text-[10px] font-normal ${priority === 'high' ? 'text-red-100' : 'text-slate-500'}`}>
                  Structure fire / rescue
                </span>
              </button>

              <button
                type="button"
                onClick={() => setPriority('medium')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'medium'
                    ? 'border-amber-500 bg-amber-500 text-white shadow-lg shadow-amber-500/30'
                    : 'border-slate-200 hover:border-amber-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🟠 Moderate</span>
                <span className={`text-[10px] font-normal ${priority === 'medium' ? 'text-amber-100' : 'text-slate-500'}`}>
                  Hazardous alarm
                </span>
              </button>

              <button
                type="button"
                onClick={() => setPriority('low')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'low'
                    ? 'border-emerald-600 bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                    : 'border-slate-200 hover:border-emerald-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🟢 Low</span>
                <span className={`text-[10px] font-normal ${priority === 'low' ? 'text-emerald-100' : 'text-slate-500'}`}>
                  Support / inspection
                </span>
              </button>
            </div>
          </div>

          {/* Starting Location + Live GPS Button */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Starting Location <span className="text-rose-500">*</span>
              </label>
              <button
                type="button"
                onClick={handleUseCurrentLocation}
                disabled={isLocating}
                className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors cursor-pointer"
              >
                <Radio className={`w-3.5 h-3.5 ${isLocating ? 'animate-spin' : 'animate-pulse'}`} />
                <span>{isLocating ? 'Acquiring GPS...' : '📍 Use My Current Location'}</span>
              </button>
            </div>

            <select
              value={startLocation}
              onChange={(e) => setStartLocation(e.target.value)}
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-100 text-slate-900 font-semibold text-sm outline-none transition-all bg-white"
            >
              {MOCK_JUNCTIONS.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.name} (Junction {j.id.replace('J', '')})
                </option>
              ))}
            </select>

            {gpsFeedback && (
              <p className="mt-2 text-xs font-medium text-blue-700 bg-blue-50/80 p-2.5 rounded-xl border border-blue-100">
                {gpsFeedback}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full py-4 px-6 rounded-2xl bg-orange-500 hover:bg-orange-600 active:scale-[0.98] text-white font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-orange-500/30 transition-all cursor-pointer"
          >
            <span>FIND BEST ROUTE</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
