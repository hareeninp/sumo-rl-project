import React, { useState } from 'react';
import { VehicleType, User } from '../types';
import { Ambulance, Flame, Siren, ArrowLeft, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface VehicleDetailsPageProps {
  onBack: () => void;
  onSaveAndProceed: (user: User) => void;
  initialUser?: User | null;
}

export const VehicleDetailsPage: React.FC<VehicleDetailsPageProps> = ({
  onBack,
  onSaveAndProceed,
  initialUser,
}) => {
  const [vehicleId, setVehicleId] = useState(initialUser?.vehicleId || 'AMB-01');
  const [licenseNo, setLicenseNo] = useState(initialUser?.licenseNumber || 'DL-9042-EMG');
  const [vehicleType, setVehicleType] = useState<VehicleType>(initialUser?.vehicleType || 'ambulance');
  const [rememberDevice, setRememberDevice] = useState(true);
  const [error, setError] = useState('');

  const handleTypeSelect = (type: VehicleType) => {
    setVehicleType(type);
    if (vehicleId === 'AMB-01' || vehicleId === 'FIRE-01' || vehicleId === 'POL-01') {
      if (type === 'ambulance') setVehicleId('AMB-01');
      if (type === 'fireEngine') setVehicleId('FIRE-01');
      if (type === 'police') setVehicleId('POL-01');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicleId.trim()) {
      setError('Please enter a valid Vehicle / Unit ID.');
      return;
    }
    if (!licenseNo.trim()) {
      setError('Please enter a vehicle license number.');
      return;
    }

    setError('');
    const user: User = {
      id: `usr_${Date.now()}`,
      vehicleId: vehicleId.trim().toUpperCase(),
      licenseNumber: licenseNo.trim().toUpperCase(),
      vehicleType,
      officerName: vehicleType === 'ambulance' ? 'Medic Operator Sarah Jenkins' : vehicleType === 'fireEngine' ? 'Captain Marcus Vance' : 'Officer David Chen',
      rememberDevice,
    };

    onSaveAndProceed(user);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 sm:p-6 text-slate-800">
      <div className="w-full max-w-lg bg-white rounded-3xl p-6 sm:p-8 shadow-xl shadow-slate-200/70 border border-slate-200/80">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button
            type="button"
            onClick={onBack}
            className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center justify-center transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900">
              Enter Vehicle Details
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 font-medium">
              Please provide your unit information to authenticate.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-semibold flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Vehicle ID */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Vehicle ID <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              placeholder="e.g. AMB-01, FIRE-01, POL-01"
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-slate-900 font-semibold text-sm outline-none transition-all"
            />
          </div>

          {/* License Number */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              License Number <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={licenseNo}
              onChange={(e) => setLicenseNo(e.target.value)}
              placeholder="e.g. DL-9042-EMG"
              className="w-full px-4 py-3.5 rounded-xl border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 text-slate-900 font-semibold text-sm outline-none transition-all"
            />
          </div>

          {/* Vehicle Type Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Vehicle Type <span className="text-rose-500">*</span>
            </label>

            <div className="grid grid-cols-3 gap-3">
              {/* Ambulance */}
              <button
                type="button"
                onClick={() => handleTypeSelect('ambulance')}
                className={`p-4 rounded-2xl border-2 flex flex-col items-center justify-center gap-2 transition-all cursor-pointer ${
                  vehicleType === 'ambulance'
                    ? 'border-red-500 bg-red-50/70 shadow-md shadow-red-500/10'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${vehicleType === 'ambulance' ? 'bg-red-500 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  <Ambulance className="w-6 h-6" />
                </div>
                <span className={`text-xs font-bold ${vehicleType === 'ambulance' ? 'text-red-700' : 'text-slate-700'}`}>
                  Ambulance
                </span>
                {vehicleType === 'ambulance' && (
                  <CheckCircle2 className="w-4 h-4 text-red-500" />
                )}
              </button>

              {/* Fire Engine */}
              <button
                type="button"
                onClick={() => handleTypeSelect('fireEngine')}
                className={`p-4 rounded-2xl border-2 flex flex-col items-center justify-center gap-2 transition-all cursor-pointer ${
                  vehicleType === 'fireEngine'
                    ? 'border-orange-500 bg-orange-50/70 shadow-md shadow-orange-500/10'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${vehicleType === 'fireEngine' ? 'bg-orange-500 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  <Flame className="w-6 h-6" />
                </div>
                <span className={`text-xs font-bold ${vehicleType === 'fireEngine' ? 'text-orange-700' : 'text-slate-700'}`}>
                  Fire Engine
                </span>
                {vehicleType === 'fireEngine' && (
                  <CheckCircle2 className="w-4 h-4 text-orange-500" />
                )}
              </button>

              {/* Police */}
              <button
                type="button"
                onClick={() => handleTypeSelect('police')}
                className={`p-4 rounded-2xl border-2 flex flex-col items-center justify-center gap-2 transition-all cursor-pointer ${
                  vehicleType === 'police'
                    ? 'border-blue-600 bg-blue-50/70 shadow-md shadow-blue-600/10'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${vehicleType === 'police' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  <Siren className="w-6 h-6" />
                </div>
                <span className={`text-xs font-bold ${vehicleType === 'police' ? 'text-blue-700' : 'text-slate-700'}`}>
                  Police
                </span>
                {vehicleType === 'police' && (
                  <CheckCircle2 className="w-4 h-4 text-blue-600" />
                )}
              </button>
            </div>
          </div>

          {/* Remember device checkbox */}
          <div className="flex items-center gap-2.5 pt-1">
            <input
              type="checkbox"
              id="remember"
              checked={rememberDevice}
              onChange={(e) => setRememberDevice(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 cursor-pointer"
            />
            <label htmlFor="remember" className="text-xs font-semibold text-slate-600 cursor-pointer flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Remember this device for persistent automatic login</span>
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full py-4 px-6 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25 transition-all cursor-pointer"
          >
            <span>Continue to Emergency Console</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
