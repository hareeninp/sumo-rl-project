import { C2Performance } from '../types';

interface Props {
  performance: C2Performance;
}

export function PerformanceDashboard({
  performance,
}: Props) {
  const cards = [
    {
      label: 'Total Events',
      value: performance.totalEvents,
    },
    {
      label: 'Active Emergencies',
      value: performance.activeEmergencies,
    },
    {
      label: 'Completed Emergencies',
      value: performance.completedEmergencies,
    },
    {
      label: 'Authorized Vehicles',
      value: performance.authorizedVehicles,
    },
    {
      label: 'Revoked Vehicles',
      value: performance.revokedVehicles,
    },
    {
      label: 'Average ETA',
      value: `${performance.averageEtaMinutes} min`,
    },
  ];

  return (
    <section className="rounded-2xl bg-slate-800 border border-slate-700 p-5 shadow-xl">
      <h2 className="text-lg font-bold text-white">
        Performance Dashboard
      </h2>

      <p className="text-xs text-slate-400 mt-1 mb-4">
        C2 operational performance
      </p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-xl bg-slate-900 p-4"
          >
            <p className="text-xs text-slate-400">
              {card.label}
            </p>

            <p className="text-2xl font-bold text-white mt-1">
              {card.value}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}