import React, { useState } from 'react';
import { EmergencyVehicle, RouteOption } from '../types';

import {
  Clock,
  Gauge,
  Activity,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  X,
  Sparkles,
  Route,
  Zap,
} from 'lucide-react';

interface RouteInfoCardProps {
  vehicle: EmergencyVehicle;

  routeOptions?: RouteOption[];

  onSelectRoute: (route: RouteOption) => void;

  onClose?: () => void;

  onOpenPriorityModal?: () => void;
}

export const RouteInfoCard: React.FC<RouteInfoCardProps> = ({
  vehicle,
  routeOptions,
  onSelectRoute,
  onClose,
  onOpenPriorityModal,
}) => {

  /* ================================
     CARD OPEN / CLOSE
  ================================= */
  const [isCardOpen, setIsCardOpen] = useState(true);

  /* ================================
     ROUTE OPTIONS OPEN / CLOSE
  ================================= */
  const [showAllRoutes, setShowAllRoutes] = useState(false);

  /* ================================
     WHY ROUTE OPEN / CLOSE
  ================================= */
  const [isWhyRouteOpen, setIsWhyRouteOpen] = useState(false);

  /* ================================
     ROUTES
  ================================= */
  const allRoutes: RouteOption[] =
    routeOptions && routeOptions.length > 0
      ? routeOptions
      : [
          vehicle.route,
          ...(vehicle.alternateRoutes || []),
        ].filter(Boolean) as RouteOption[];


  /* ============================================================
     MINIMIZED CARD
     ============================================================ */

  if (!isCardOpen) {
    return (
      <div className="relative">

        {/* Small button when card is minimized */}
        <button
          type="button"
          onClick={() => setIsCardOpen(true)}
          title="Open vehicle information"
          className="
            w-11
            h-11
            rounded-xl
            bg-white/95
            backdrop-blur-md
            border
            border-slate-200
            shadow-xl
            flex
            items-center
            justify-center
            text-slate-700
            hover:bg-slate-50
            hover:scale-105
            transition-all
            cursor-pointer
          "
        >
          <ChevronUp className="w-5 h-5" />
        </button>

      </div>
    );
  }


  /* ============================================================
     FULL CARD
     ============================================================ */

  const displayEta =
    vehicle.remainingEtaMinutes !== undefined
      ? vehicle.remainingEtaMinutes <= 0
        ? '0'
        : vehicle.remainingEtaMinutes < 1
        ? '< 1'
        : String(Math.round(vehicle.remainingEtaMinutes))
      : String(Math.max(1, Math.round(vehicle.route?.etaMinutes || 8)));

  const displayDistance =
    vehicle.remainingDistanceKm !== undefined
      ? vehicle.remainingDistanceKm <= 0
        ? '0.0'
        : vehicle.remainingDistanceKm.toFixed(1)
      : String(vehicle.route?.totalDistanceKm || 3.2);

  return (
    <div
      className="
        relative
        w-full
        sm:w-80
        bg-white/95
        backdrop-blur-md
        rounded-2xl
        shadow-xl
        border border-slate-200
        p-4
        flex
        flex-col
        gap-3
        text-slate-800
        animate-in
        fade-in
        slide-in-from-right-4
        duration-200
      "
    >

      {/* ========================================================
          TOP HEADER
      ======================================================== */}

      <div
        className="
          flex
          items-start
          justify-between
          pb-3
          border-b
          border-slate-100
        "
      >

        {/* Vehicle information */}
        <div className="flex items-center gap-2.5">

          <div
            className={`
              w-10
              h-10
              rounded-xl
              flex
              items-center
              justify-center
              font-black
              text-white
              text-xs
              shadow-md

              ${
                vehicle.type === 'ambulance'
                  ? 'bg-red-600 shadow-red-500/20'
                  : vehicle.type === 'fireEngine'
                  ? 'bg-orange-500 shadow-orange-500/20'
                  : 'bg-blue-600 shadow-blue-500/20'
              }
            `}
          >
            {vehicle.id}
          </div>


          <div>

            <div
              className="
                text-[10px]
                uppercase
                font-extrabold
                text-slate-400
              "
            >
              En Route To
            </div>

            <h4
              className="
                text-sm
                font-black
                text-slate-900
                leading-tight
                truncate
                max-w-[180px]
              "
            >
              {vehicle.destinationName}
            </h4>

          </div>

        </div>


        {/* Header buttons */}
        <div className="flex items-center gap-1.5">

          {/* Priority Score */}
          {onOpenPriorityModal && (
            <button
              type="button"
              onClick={onOpenPriorityModal}
              className={`
                px-2.5
                py-1
                rounded-lg
                text-[11px]
                font-black
                uppercase
                tracking-wider
                flex
                items-center
                gap-1
                transition-transform
                hover:scale-105

                ${
                  vehicle.priorityStatus === 'FAVOURED'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-slate-100 text-slate-700 border border-slate-300'
                }
              `}
            >

              <Zap
                className="
                  w-3
                  h-3
                  text-amber-500
                  fill-amber-500
                "
              />

              <span>
                Score: {vehicle.priorityScore}
              </span>

            </button>
          )}


          {/* ==================================================
              MINIMIZE CARD BUTTON
          ================================================== */}

          <button
            type="button"
            onClick={() => setIsCardOpen(false)}
            title="Minimize"
            className="
              p-1.5
              rounded-lg
              text-slate-500
              hover:text-slate-900
              hover:bg-slate-100
              transition-all
              cursor-pointer
            "
          >
            <ChevronDown className="w-4 h-4" />
          </button>


          {/* Close button */}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Close"
              className="
                p-1
                rounded-lg
                text-slate-400
                hover:text-slate-700
                hover:bg-slate-100
                transition-colors
                cursor-pointer
              "
            >
              <X className="w-4 h-4" />
            </button>
          )}

        </div>

      </div>


      {/* ========================================================
          METRICS
      ======================================================== */}

      <div
        className="
          grid
          grid-cols-2
          gap-2.5
          bg-slate-50
          p-3
          rounded-xl
          border
          border-slate-200/80
        "
      >

        {/* ETA */}
        <div>

          <div
            className="
              text-[10px]
              uppercase
              font-bold
              text-slate-400
              flex
              items-center
              gap-1
              mb-1
            "
          >
            <Clock className="w-3 h-3" />
            <span>ETA</span>
          </div>

          <div
            className="
              text-2xl
              font-black
              text-slate-900
              leading-none
            "
          >
            {displayEta}

            <span
              className="
                text-xs
                font-bold
                text-slate-500
                ml-1
              "
            >
              min
            </span>

          </div>

        </div>


        {/* Distance */}
        <div>

          <div
            className="
              text-[10px]
              uppercase
              font-bold
              text-slate-400
              flex
              items-center
              gap-1
              mb-1
            "
          >
            <Route className="w-3 h-3" />
            <span>Distance</span>
          </div>

          <div
            className="
              text-xl
              font-extrabold
              text-slate-900
              leading-none
            "
          >
            {displayDistance}

            <span
              className="
                text-xs
                font-bold
                text-slate-500
                ml-1
              "
            >
              km
            </span>

          </div>

        </div>


        {/* Speed */}
        <div
          className="
            pt-2
            border-t
            border-slate-200/60
          "
        >

          <div
            className="
              text-[10px]
              uppercase
              font-bold
              text-slate-400
              flex
              items-center
              gap-1
              mb-1
            "
          >
            <Gauge className="w-3 h-3" />
            <span>Speed</span>
          </div>

          <div
            className="
              text-sm
              font-black
              text-slate-800
            "
          >

            {vehicle.speedKmh}

            <span
              className="
                text-[10px]
                font-normal
                text-slate-500
                ml-1
              "
            >
              km/h
            </span>

          </div>

        </div>


        {/* Traffic */}
        <div
          className="
            pt-2
            border-t
            border-slate-200/60
          "
        >

          <div
            className="
              text-[10px]
              uppercase
              font-bold
              text-slate-400
              flex
              items-center
              gap-1
              mb-1
            "
          >
            <Activity className="w-3 h-3" />
            <span>Traffic</span>
          </div>

          <div
            className={`
              text-sm
              font-black

              ${
                vehicle.route?.trafficSummary === 'Clear'
                  ? 'text-emerald-600'
                  : 'text-amber-600'
              }
            `}
          >
            {vehicle.route?.trafficSummary || 'Clear'}
          </div>

        </div>

      </div>


      {/* ========================================================
          GREEN CORRIDOR
      ======================================================== */}

      <div
        className="
          flex
          items-center
          justify-between
          px-3
          py-2
          rounded-xl
          bg-emerald-50
          border
          border-emerald-200
          text-emerald-800
          text-xs
          font-bold
        "
      >

        <div className="flex items-center gap-1.5">

          <span
            className="
              w-2.5
              h-2.5
              rounded-full
              bg-emerald-500
              shrink-0
            "
          />

          <span>
            Green Corridor
          </span>

        </div>

        <span
          className="
            text-[11px]
            font-black
            uppercase
            tracking-wider
            text-emerald-700
          "
        >
          ACTIVE
        </span>

      </div>


      {/* ========================================================
          ROUTE OPTIONS
      ======================================================== */}

      <div
        className="
          border-t
          border-slate-100
          pt-3
        "
      >

        <button
          type="button"
          onClick={() =>
            setShowAllRoutes(!showAllRoutes)
          }
          className="
            w-full
            flex
            items-center
            justify-between
            text-xs
            font-black
            uppercase
            tracking-wider
            text-slate-700
            hover:text-slate-900
            transition-colors
            cursor-pointer
          "
        >

          <div className="flex items-center gap-1.5">

            <Route
              className="
                w-3.5
                h-3.5
                text-blue-600
              "
            />

            <span>
              Route Options
            </span>

          </div>


          {showAllRoutes ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}

        </button>


        {/* Route list */}
        {showAllRoutes && (
          <div className="mt-2 space-y-1.5">

            {allRoutes.map((rt) => {

              const isCurrent =
                vehicle.route?.id === rt.id;

              return (
                <div
                  key={rt.id}
                  onClick={() =>
                    onSelectRoute(rt)
                  }
                  className={`
                    p-2.5
                    rounded-xl
                    border-2
                    cursor-pointer
                    transition-all
                    flex
                    items-center
                    justify-between
                    text-xs

                    ${
                      isCurrent
                        ? 'border-emerald-500 bg-emerald-50/40'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }
                  `}
                >

                  <div className="flex items-center gap-2">

                    <div
                      className="
                        w-2.5
                        h-2.5
                        rounded-full
                        shrink-0
                      "
                      style={{
                        backgroundColor: rt.color,
                      }}
                    />

                    <div>

                      <div
                        className="
                          font-bold
                          text-slate-900
                          leading-tight
                        "
                      >
                        {rt.name}
                      </div>

                      <div
                        className="
                          text-[10px]
                          text-slate-500
                        "
                      >
                        {rt.isRecommended
                          ? 'Optimal signals & ETA'
                          : `${rt.trafficSummary} traffic`}
                      </div>

                    </div>

                  </div>


                  <div
                    className="
                      text-right
                      shrink-0
                    "
                  >

                    <div
                      className="
                        font-black
                        text-slate-900
                      "
                    >
                      {Math.round(rt.etaMinutes)} min
                    </div>

                    <div
                      className="
                        text-[10px]
                        text-slate-500
                      "
                    >
                      {rt.totalDistanceKm} km
                    </div>

                  </div>

                </div>
              );
            })}

          </div>
        )}

      </div>


      {/* ========================================================
          WHY CHOOSE THIS ROUTE
      ======================================================== */}

      <div
        className="
          border-t
          border-slate-100
          pt-3
        "
      >

        <button
          type="button"
          onClick={() =>
            setIsWhyRouteOpen(!isWhyRouteOpen)
          }
          className="
            w-full
            flex
            items-center
            justify-between
            text-xs
            font-black
            uppercase
            tracking-wider
            text-slate-700
            hover:text-slate-900
            transition-colors
            cursor-pointer
          "
        >

          <div className="flex items-center gap-1.5">

            <Sparkles
              className="
                w-3.5
                h-3.5
                text-amber-500
              "
            />

            <span>
              Why choose this route?
            </span>

          </div>


          {isWhyRouteOpen ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}

        </button>


        {/* Reasons */}
        {isWhyRouteOpen && (
          <div
            className="
              mt-2.5
              space-y-1.5
              text-xs
              text-slate-600
              bg-slate-50/80
              p-3
              rounded-xl
              border
              border-slate-200/70
            "
          >

            {vehicle.route?.reasons &&
            vehicle.route.reasons.length > 0 ? (

              vehicle.route.reasons.map(
                (reason, idx) => (

                  <div
                    key={idx}
                    className="
                      flex
                      items-start
                      gap-2
                      leading-relaxed
                    "
                  >

                    <CheckCircle2
                      className="
                        w-3.5
                        h-3.5
                        text-emerald-600
                        shrink-0
                        mt-0.5
                      "
                    />

                    <span className="font-medium">
                      {reason}
                    </span>

                  </div>

                )
              )

            ) : (

              <div
                className="
                  flex
                  items-start
                  gap-2
                  leading-relaxed
                "
              >

                <CheckCircle2
                  className="
                    w-3.5
                    h-3.5
                    text-emerald-600
                    shrink-0
                    mt-0.5
                  "
                />

                <span className="font-medium">
                  Lowest current travel time and dynamic
                  green corridor preemption.
                </span>

              </div>

            )}

          </div>
        )}

      </div>

    </div>
  );
};