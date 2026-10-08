import { C2Event } from '../types';

interface Props {
  events: C2Event[];
}

export function EventTimeline({ events }: Props) {
  return (
    <section className="rounded-2xl bg-slate-800 border border-slate-700 p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">
            Event Timeline
          </h2>

          <p className="text-xs text-slate-400">
            Disaster and emergency activity
          </p>
        </div>

        <span className="text-xs text-slate-400">
          {events.length} events
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto space-y-3">
        {events.length === 0 ? (
          <p className="text-sm text-slate-400">
            No events recorded yet.
          </p>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              className="relative pl-4 border-l-2 border-blue-500"
            >
              <p className="text-sm font-semibold text-white">
                {event.title}
              </p>

              <p className="text-xs text-slate-400">
                {event.description}
              </p>

              <p className="text-[11px] text-slate-500 mt-1">
                {new Date(
                  event.timestamp
                ).toLocaleString()}
              </p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}