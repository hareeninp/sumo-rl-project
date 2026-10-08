import React, { useState } from 'react';
import { User, PriorityLevel, Hospital } from '../types';
import { PATIENT_CONDITIONS } from '../data/mock/mockConditionsList';
import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';
import { MOCK_HOSPITALS } from '../data/mock/mockHospitals';
import { geoService } from '../services/geoService';
import { hospitalService } from '../services/hospitalService';
import {
  Ambulance,
  MapPin,
  Building2,
  ArrowRight,
  ArrowLeft,
  Radio,
  Clock,
  Sparkles,
  AlertCircle,
} from 'lucide-react';

interface AmbulanceEmergencyFormProps {
  user: User;
  onBack?: () => void;
  onSubmit: (data: {
    patientCondition: string;
    priority: PriorityLevel;
    startLocationJunctionId: string;
    destinationName: string;
    destinationJunctionId: string;
    selectedHospital: Hospital;
    isUsingLiveGps: boolean;
    liveGpsCoords?: { lat: number; lng: number };
  }) => void;
}

export const AmbulanceEmergencyForm: React.FC<AmbulanceEmergencyFormProps> = ({
  user,
  onBack,
  onSubmit,
}) => {
  const [patientCondition, setPatientCondition] = useState(PATIENT_CONDITIONS[0].name);
  const [priority, setPriority] = useState<PriorityLevel>('high');
  const [startLocation, setStartLocation] = useState('J1');
  const [selectedHospitalId, setSelectedHospitalId] = useState('H1');
  const [isLocating, setIsLocating] = useState(false);
  const [gpsFeedback, setGpsFeedback] = useState<string | null>(null);
  const [liveCoords, setLiveCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  // Find suitable hospitals for current condition
  const suitableHospitals = hospitalService.findSuitableHospitals(patientCondition);
  const bestHospitalMatch = hospitalService.selectBestHospital(patientCondition, startLocation);

  const handleConditionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCondition = e.target.value;
    setPatientCondition(newCondition);
    // Auto update selected hospital based on smart matching
    const match = hospitalService.selectBestHospital(newCondition, startLocation);
    setSelectedHospitalId(match.hospital.id);
  };

  // Section 77: 📍 Use My Current Location
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
    if (!patientCondition) errs.push('Please select the patient condition.');
    if (!priority) errs.push('Please select emergency priority.');
    if (!startLocation) errs.push('Please select a starting location.');

    if (errs.length > 0) {
      setErrors(errs);
      return;
    }

    setErrors([]);
    const chosenHospital =
      MOCK_HOSPITALS.find((h) => h.id === selectedHospitalId) || bestHospitalMatch.hospital;

    onSubmit({
      patientCondition,
      priority,
      startLocationJunctionId: startLocation,
      destinationName: chosenHospital.name,
      destinationJunctionId: chosenHospital.junctionId,
      selectedHospital: chosenHospital,
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
            <div className="w-12 h-12 rounded-2xl bg-red-500 text-white flex items-center justify-center shadow-lg shadow-red-500/25 shrink-0">
              <Ambulance className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900">
                  AMBULANCE EMERGENCY
                </h2>
                <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-red-100 text-red-700">
                  {user.vehicleId}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 font-medium">
                Enter patient details to calculate the fastest green corridor to the nearest suitable hospital.
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
          {/* Patient Condition Dropdown (15 options) */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Patient Condition <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <select
                value={patientCondition}
                onChange={handleConditionChange}
                className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-red-500 focus:ring-2 focus:ring-red-100 text-slate-900 font-semibold text-sm outline-none transition-all bg-white"
              >
                {PATIENT_CONDITIONS.map((cond) => (
                  <option key={cond.id} value={cond.name}>
                    {cond.name}
                  </option>
                ))}
              </select>
            </div>
            <p className="mt-1.5 text-xs text-slate-500 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Smart matching automatically filters certified emergency trauma centers.</span>
            </p>
          </div>

          {/* Emergency Priority Selector (High, Medium, Low) */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Emergency Severity Priority <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-3">
              {/* High */}
              <button
                type="button"
                onClick={() => setPriority('high')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'high'
                    ? 'border-red-600 bg-red-600 text-white shadow-lg shadow-red-600/30'
                    : 'border-slate-200 hover:border-red-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🔴 Critical (High)</span>
                <span className={`text-[10px] font-normal ${priority === 'high' ? 'text-red-100' : 'text-slate-500'}`}>
                  Immediate response
                </span>
              </button>

              {/* Medium */}
              <button
                type="button"
                onClick={() => setPriority('medium')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'medium'
                    ? 'border-amber-500 bg-amber-500 text-white shadow-lg shadow-amber-500/30'
                    : 'border-slate-200 hover:border-amber-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🟠 Urgent (Medium)</span>
                <span className={`text-[10px] font-normal ${priority === 'medium' ? 'text-amber-100' : 'text-slate-500'}`}>
                  Rapid response
                </span>
              </button>

              {/* Low */}
              <button
                type="button"
                onClick={() => setPriority('low')}
                className={`py-3.5 px-3 rounded-2xl border-2 font-bold text-xs sm:text-sm flex flex-col items-center gap-1 transition-all cursor-pointer ${
                  priority === 'low'
                    ? 'border-emerald-600 bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                    : 'border-slate-200 hover:border-emerald-300 bg-slate-50/50 text-slate-700'
                }`}
              >
                <span>🟢 Non-critical (Low)</span>
                <span className={`text-[10px] font-normal ${priority === 'low' ? 'text-emerald-100' : 'text-slate-500'}`}>
                  Standard dispatch
                </span>
              </button>
            </div>
          </div>

          {/* Section 77: Starting Location + Live GPS Button */}
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

            <div className="relative">
              <select
                value={startLocation}
                onChange={(e) => setStartLocation(e.target.value)}
                className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-red-500 focus:ring-2 focus:ring-red-100 text-slate-900 font-semibold text-sm outline-none transition-all bg-white"
              >
                {MOCK_JUNCTIONS.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.name} (Junction {j.id.replace('J', '')})
                  </option>
                ))}
              </select>
            </div>

            {gpsFeedback && (
              <p className="mt-2 text-xs font-medium text-blue-700 bg-blue-50/80 p-2.5 rounded-xl border border-blue-100">
                {gpsFeedback}
              </p>
            )}
          </div>

          {/* Destination / Hospital Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Destination Medical Center <span className="text-rose-500">*</span>
            </label>

            <div className="space-y-2">
              {suitableHospitals.map((h) => {
                const etaStats = hospitalService.calculateHospitalETA(startLocation, h);
                const isSelected = selectedHospitalId === h.id;
                const isBest = bestHospitalMatch.hospital.id === h.id;

                return (
                  <div
                    key={h.id}
                    onClick={() => setSelectedHospitalId(h.id)}
                    className={`p-3.5 rounded-2xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                      isSelected
                        ? 'border-red-500 bg-red-50/50 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${isSelected ? 'bg-red-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                        <Building2 className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">{h.name}</span>
                          {isBest && (
                            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                              Fastest Suitable
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500">
                          {h.specialties.slice(0, 2).join(' • ')}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="font-black text-sm text-slate-900 flex items-center justify-end gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{etaStats.etaMin} min</span>
                      </div>
                      <span className="text-xs text-slate-500 font-medium">{etaStats.distanceKm} km</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full py-4 px-6 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-[0.98] text-white font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-red-600/30 transition-all cursor-pointer"
          >
            <span>FIND BEST ROUTE</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
