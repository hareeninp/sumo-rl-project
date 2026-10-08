import { GreenCorridorState } from '../types';
import { MOCK_JUNCTIONS } from '../data/mock/mockJunctions';

/**
 * Team 2 Integration Service
 * Signal Preemption & Green Corridor controller bridge
 */
export const team2Service = {
  getControlledJunctions(pathJunctionIds: string[], currentProgressPercent: number): GreenCorridorState['junctions'] {
    const totalJuncs = pathJunctionIds.length;
    const currentIndex = Math.floor((currentProgressPercent / 100) * totalJuncs);

    return pathJunctionIds.map((jId, idx) => {
      let signalState: 'green' | 'red' | 'yellow' = 'green';
      let preemption: 'STANDBY' | 'REQUESTED' | 'ACTIVE' | 'COMPLETED' = 'STANDBY';
      let recoveryStatus: 'PENDING' | 'ACTIVE' | 'RECOVERED' = 'PENDING';

      if (idx < currentIndex) {
        // Already passed
        signalState = 'green';
        preemption = 'COMPLETED';
        recoveryStatus = 'RECOVERED';
      } else if (idx === currentIndex) {
        // At or immediately approaching junction
        signalState = 'green';
        preemption = 'ACTIVE';
        recoveryStatus = 'ACTIVE';
      } else if (idx === currentIndex + 1) {
        // Next in corridor
        signalState = 'green';
        preemption = 'REQUESTED';
        recoveryStatus = 'PENDING';
      } else {
        signalState = 'green';
        preemption = 'STANDBY';
        recoveryStatus = 'PENDING';
      }

      return {
        junctionId: jId,
        signalState,
        preemption,
        recoveryStatus,
      };
    });
  },

  getGreenCorridorStatus(vehicleId: string, pathJunctionIds: string[], progress: number): GreenCorridorState {
    return {
      corridorId: `gc-${vehicleId}-${pathJunctionIds.join('-')}`,
      vehicleId,
      isActive: true,
      junctions: this.getControlledJunctions(pathJunctionIds, progress),
    };
  },

  getAllJunctionSignals() {
    return MOCK_JUNCTIONS.map((j) => ({
      junctionId: j.id,
      signalState: j.signalState,
      preemptionStatus: j.preemptionStatus,
    }));
  },
};
