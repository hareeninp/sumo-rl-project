import React, { useState } from 'react';
import { User, VehicleType } from '../types';
import {
  Shield,
  Ambulance,
  Flame,
  Siren,
  User as UserIcon,
  LogOut,
  Radio,
  ChevronDown,
  CheckCircle2,
  ArrowLeft,
  Compass,
  ExternalLink,
} from 'lucide-react';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
  onNavigateNewEmergency: () => void;
  gpsStatus: 'STRONG' | 'MEDIUM' | 'WEAK' | 'UNAVAILABLE';
  onBack?: () => void;
  canGoBack?: boolean;
  onOpenGoogleMaps?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onLogout,
  onNavigateNewEmergency,
  gpsStatus,
  onBack,
  canGoBack,
  onOpenGoogleMaps,
}) => {
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const getVehicleBadge = (type: VehicleType) => {
    switch (type) {
      case 'ambulance':
        return {
          icon: Ambulance,
          label: 'AMBULANCE UNIT',
          color: 'bg-red-50 text-red-700 border-red-200',
          iconColor: 'text-red-600',
        };

      case 'fireEngine':
        return {
          icon: Flame,
          label: 'FIRE & RESCUE UNIT',
          color: 'bg-orange-50 text-orange-700 border-orange-200',
          iconColor: 'text-orange-600',
        };

      case 'police':
        return {
          icon: Siren,
          label: 'POLICE PATROL UNIT',
          color: 'bg-blue-50 text-blue-700 border-blue-200',
          iconColor: 'text-blue-600',
        };
    }
  };

  const badge = user ? getVehicleBadge(user.vehicleType) : null;

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-6 py-2.5 flex items-center justify-between shadow-xs sticky top-0 z-40">

      {/* =====================================================
          LEFT: BACK BUTTON + BRAND
          ===================================================== */}
      <div className="flex items-center gap-2 sm:gap-3">

        {canGoBack && onBack && (
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-800 font-bold text-xs shadow-xs border border-slate-200/80 transition-all cursor-pointer group"
            title="Go to previous page"
          >
            <ArrowLeft className="w-4 h-4 text-slate-700 group-hover:-translate-x-0.5 transition-transform" />

            <span className="hidden xs:inline sm:inline">
              Back
            </span>
          </button>
        )}

        <button
          type="button"
          onClick={onNavigateNewEmergency}
          className="flex items-center gap-2.5 text-left group transition-all"
        >

          {/* Logo */}
          <div className="w-10 h-10 rounded-xl bg-linear-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5" />
          </div>

          {/* Brand */}
          <div>

            <div className="flex items-center gap-1.5">

              <span className="font-black tracking-tight text-slate-900 text-lg">
                ResQ<span className="text-blue-600">Route</span>
              </span>

            </div>

            <p className="text-xs text-slate-500 font-medium hidden sm:block">
              Smart Emergency Routing & Green Corridor
            </p>

          </div>
        </button>
      </div>


      {/* =====================================================
          CENTER: GPS STATUS + GOOGLE MAPS
          ===================================================== */}
      <div className="flex items-center gap-2">

        {/* GPS Status */}
        <div className="hidden md:flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1 rounded-full text-xs font-semibold">

          <Radio
            className={`w-3.5 h-3.5 ${
              gpsStatus === 'STRONG'
                ? 'text-emerald-600 animate-pulse'
                : gpsStatus === 'WEAK'
                ? 'text-amber-500'
                : 'text-slate-400'
            }`}
          />

          <span className="text-slate-600">
            GPS:
          </span>

          <span
            className={`${
              gpsStatus === 'STRONG'
                ? 'text-emerald-700 font-bold'
                : gpsStatus === 'WEAK'
                ? 'text-amber-700 font-bold'
                : 'text-slate-500'
            }`}
          >
            {gpsStatus}
          </span>

        </div>


        {/* Google Maps */}
        {onOpenGoogleMaps && (
          <button
            type="button"
            onClick={onOpenGoogleMaps}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs border border-blue-200 transition-all cursor-pointer"
            title="Open Route in Google Maps"
          >

            <Compass className="w-3.5 h-3.5 text-blue-600" />

            <span>
              Google Maps
            </span>

            <ExternalLink className="w-3 h-3 opacity-70" />

          </button>
        )}

      </div>


      {/* =====================================================
          RIGHT: VEHICLE UNIT + USER MENU
          ===================================================== */}
      <div className="flex items-center gap-2 sm:gap-3">

        {/* Vehicle Badge */}
        {user && badge && (
          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold ${badge.color}`}
          >

            <badge.icon
              className={`w-4 h-4 ${badge.iconColor}`}
            />

            <div>

              <div className="font-extrabold leading-none">
                {user.vehicleId}
              </div>

              <div className="text-[10px] opacity-80 leading-tight">
                {badge.label}
              </div>

            </div>

          </div>
        )}


        {/* User Menu */}
        {user ? (

          <div className="relative">

            <button
              type="button"
              onClick={() =>
                setShowProfileMenu(
                  !showProfileMenu
                )
              }
              className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors"
            >

              <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs">
                {user.vehicleId.slice(0, 2)}
              </div>

              <span className="hidden lg:inline text-slate-800 font-semibold">
                {user.vehicleId}
              </span>

              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />

            </button>


            {/* Profile Dropdown */}
            {showProfileMenu && (

              <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">

                {/* User Information */}
                <div className="px-4 py-2 border-b border-slate-100">

                  <p className="text-xs text-slate-400 font-medium">
                    Logged in as
                  </p>

                  <p className="text-sm font-bold text-slate-800">
                    {user.vehicleId}
                  </p>

                  <p className="text-xs text-slate-500">
  {user.vehicleType === 'ambulance'
    ? 'Ambulance Operator'
    : user.vehicleType === 'fireEngine'
    ? 'Fire Engine Operator'
    : 'Police Operator'}
</p>

                  <div className="mt-1 flex items-center gap-1 text-[11px] text-emerald-600 font-medium">

                    <CheckCircle2 className="w-3 h-3" />

                    <span>
                      Device Remembered
                    </span>

                  </div>

                </div>


                {/* Menu Actions */}
                <div className="py-1">

                  {/* Google Maps */}
                  {onOpenGoogleMaps && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowProfileMenu(false);
                        onOpenGoogleMaps();
                      }}
                      className="w-full text-left px-4 py-2 text-xs text-blue-700 hover:bg-blue-50 flex items-center gap-2 font-bold"
                    >

                      <Compass className="w-3.5 h-3.5 text-blue-600" />

                      Open Route in Google Maps

                    </button>
                  )}


                  {/* New Emergency */}
                  <button
                    type="button"
                    onClick={() => {
                      setShowProfileMenu(false);
                      onNavigateNewEmergency();
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2 font-medium"
                  >

                    <Shield className="w-3.5 h-3.5 text-blue-600" />

                    New Emergency Dispatch

                  </button>

                </div>


                {/* Logout */}
                <div className="border-t border-slate-100 pt-1">

                  <button
                    type="button"
                    onClick={() => {
                      setShowProfileMenu(false);
                      onLogout();
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 flex items-center gap-2 font-semibold"
                  >

                    <LogOut className="w-3.5 h-3.5" />

                    Logout Unit

                  </button>

                </div>

              </div>
            )}

          </div>

        ) : (

          <div className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">

            <UserIcon className="w-4 h-4" />

            <span>
              Not Signed In
            </span>

          </div>

        )}

      </div>

    </header>
  );
};