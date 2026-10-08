import { useState } from 'react';
import { DisasterMode } from '../types';

interface Props {
  disaster: DisasterMode;
  onActivate: (
    type: string,
    description: string
  ) => void;
  onDeactivate: () => void;
}

export function DisasterModePanel({
  disaster,
  onActivate,
  onDeactivate,
}: Props) {
  const [type, setType] = useState('Flood');
  const [description, setDescription] = useState('');

  const active = disaster.status === 'ACTIVE';

  return (
    <section className="rounded-2xl bg-slate-800 border border-slate-700 p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">
            Disaster Mode
          </h2>

          <p className="text-xs text-slate-400">
            C2 emergency coordination control
          </p>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-bold ${
            active
              ? 'bg-red-500/20 text-red-300'
              : 'bg-slate-700 text-slate-300'
          }`}
        >
          {active ? 'ACTIVE' : 'INACTIVE'}
        </span>
      </div>

      {active ? (
        <>
          <div className="space-y-2 text-sm text-slate-300">
            <p>
              <strong>Type:</strong>{' '}
              {disaster.disasterType}
            </p>

            <p>
              <strong>Description:</strong>{' '}
              {disaster.description || 'No description'}
            </p>

            <p>
              <strong>Activated by:</strong>{' '}
              {disaster.activatedBy || 'Unknown'}
            </p>

            <p>
              <strong>Time:</strong>{' '}
              {disaster.activatedAt
                ? new Date(
                    disaster.activatedAt
                  ).toLocaleString()
                : '-'}
            </p>
          </div>

          <button
            onClick={onDeactivate}
            className="mt-5 w-full rounded-lg bg-slate-700 hover:bg-slate-600 px-4 py-2 font-semibold"
          >
            Deactivate Disaster Mode
          </button>
        </>
      ) : (
        <div className="space-y-3">
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
          >
            <option>Flood</option>
            <option>Earthquake</option>
            <option>Fire</option>
            <option>Cyclone</option>
            <option>Major Accident</option>
            <option>Other</option>
          </select>

          <textarea
            value={description}
            onChange={(e) =>
              setDescription(e.target.value)
            }
            placeholder="Describe the disaster..."
            className="w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-white"
            rows={3}
          />

          <button
            onClick={() => {
              onActivate(type, description);
              setDescription('');
            }}
            className="w-full rounded-lg bg-red-600 hover:bg-red-500 px-4 py-2 font-bold text-white"
          >
            Activate Disaster Mode
          </button>
        </div>
      )}
    </section>
  );
}