import { User, VehicleType } from '../types';

const STORAGE_KEY = 'resqroute_auth_session';

export const authService = {
  login(vehicleId: string, _password?: string, vehicleTypeParam?: VehicleType, rememberDevice = true): User {
    const trimmedId = vehicleId.trim().toUpperCase();
    
    let type: VehicleType = vehicleTypeParam || 'ambulance';
    if (!vehicleTypeParam) {
      if (trimmedId.startsWith('FIRE') || trimmedId.startsWith('F-') || trimmedId.startsWith('ENG')) {
        type = 'fireEngine';
      } else if (trimmedId.startsWith('POL') || trimmedId.startsWith('COP') || trimmedId.startsWith('P-')) {
        type = 'police';
      } else {
        type = 'ambulance';
      }
    }

    const licenseNumber = `DL-${Math.floor(1000 + Math.random() * 9000)}-${trimmedId.replace(/[^A-Z0-9]/g, '') || '01'}`;

    const user: User = {
      id: `usr_${Date.now()}`,
      vehicleId: trimmedId || (type === 'ambulance' ? 'AMB-01' : type === 'fireEngine' ? 'FIRE-01' : 'POL-01'),
      licenseNumber,
      vehicleType: type,
      officerName: type === 'ambulance' ? 'Medic Operator Sarah Jenkins' : type === 'fireEngine' ? 'Captain Marcus Vance' : 'Officer David Chen',
      rememberDevice,
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    } catch {
      // storage unavailable fallback
    }

    return user;
  },

  logout(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  },

  getCurrentUser(): User | null {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return null;
      return JSON.parse(data) as User;
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return this.getCurrentUser() !== null;
  },

  restoreSession(): User | null {
    return this.getCurrentUser();
  },
};
