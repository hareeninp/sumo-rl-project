import { useState } from 'react';
import {
  AuthorizedVehicle,
  VehicleType,
} from '../types';

interface Props {
  vehicles: AuthorizedVehicle[];
  onRegister: (data: {
    vehicleId: string;
    vehicleType: VehicleType;
    licensePlate: string;
    authority: AuthorizedVehicle['authority'];
  }) => void;
  onRevoke: (vehicleId: string) => void;
}

export function AuthorizedVehicleRegistry({
  vehicles,
  onRegister,
  onRevoke,
}: Props) {
  const [vehicleId, setVehicleId] = useState('');
  const [licensePlate, setLicensePlate] = useState('');
  const [vehicleType, setVehicleType] =
    useState<VehicleType>('ambulance');
  const [authority, setAuthority] =
    useState<AuthorizedVehicle['authority']>(
      'hospital'
    );

  const handleRegister = () => {
    if (!vehicleId.trim() || !licensePlate.trim()) {
      return;
    }

    onRegister({
      vehicleId,
      vehicleType,
      licensePlate,
      authority,
    });

    setVehicleId('');
    setLicensePlate('');
  };

  return (
    <section className="rounded-2xl bg-slate-800 border border-slate-700 p-5 shadow-xl">
      <h2 className="text-lg font-bold text-white">
        Authorized Vehicle Registry
      </h2>

      <p className="text-xs text-slate-400 mt-1 mb-4">
        F2 authorized emergency vehicle control
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-5">
        <input
          value={vehicleId}
          onChange={(e) =>
            setVehicleId(e.target.value)
          }
          placeholder="Vehicle ID"
          className="rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
        />

        <input
          value={licensePlate}
          onChange={(e) =>
            setLicensePlate(e.target.value)
          }
          placeholder="License plate"
          className="rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
        />

        <select
          value={vehicleType}
          onChange={(e) =>
            setVehicleType(
              e.target.value as VehicleType
            )
          }
          className="rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
        >
          <option value="ambulance">
            Ambulance
          </option>
          <option value="fireEngine">
            Fire Engine
          </option>
          <option value="police">
            Police
          </option>
        </select>

        <select
          value={authority}
          onChange={(e) =>
            setAuthority(
              e.target.value as AuthorizedVehicle['authority']
            )
          }
          className="rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
        >
          <option value="hospital">Hospital</option>
          <option value="police">Police</option>
          <option value="disaster_authority">
            Disaster Authority
          </option>
        </select>

        <button
          onClick={handleRegister}
          className="md:col-span-2 rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 font-bold text-white"
        >
          Register Vehicle
        </button>
      </div>

      <div className="space-y-2">
        {vehicles.length === 0 && (
          <p className="text-sm text-slate-400">
            No vehicles registered.
          </p>
        )}

        {vehicles.map((vehicle) => (
          <div
            key={vehicle.id}
            className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 rounded-lg bg-slate-900 p-3"
          >
            <div>
              <p className="font-semibold text-white">
                {vehicle.vehicleId}
              </p>

              <p className="text-xs text-slate-400">
                {vehicle.vehicleType} •{' '}
                {vehicle.licensePlate}
              </p>

              <p className="text-xs text-slate-500">
                Authority: {vehicle.authority}
              </p>
            </div>

            {vehicle.authorized ? (
              <button
                onClick={() =>
                  onRevoke(vehicle.vehicleId)
                }
                className="rounded-lg bg-red-600/20 text-red-300 px-3 py-2 text-sm font-semibold"
              >
                Revoke
              </button>
            ) : (
              <span className="rounded-lg bg-slate-700 text-slate-400 px-3 py-2 text-sm">
                Revoked
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}