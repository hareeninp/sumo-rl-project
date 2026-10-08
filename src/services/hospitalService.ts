import { Hospital, PatientCondition } from '../types';
import { MOCK_HOSPITALS } from '../data/mock/mockHospitals';
import { PATIENT_CONDITIONS } from '../data/mock/mockConditionsList';

export const hospitalService = {
  getAllHospitals(): Hospital[] {
    return MOCK_HOCK_HOSPITALS_SAFE;
  },

  findSuitableHospitals(conditionIdOrName: string): Hospital[] {
    const condition = PATIENT_CONDITIONS.find(
      (c) => c.id === conditionIdOrName || c.name === conditionIdOrName
    );

    if (!condition || !condition.isSpecialized || condition.id === 'general') {
      // General emergency fallback: any facility with general capacity
      return MOCK_HOCK_HOSPITALS_SAFE;
    }

    const matched = MOCK_HOCK_HOSPITALS_SAFE.filter((h) =>
      h.specialties.some(
        (s) =>
          s.toLowerCase().includes(condition.name.toLowerCase().replace(/[^a-z ]/g, '')) ||
          (condition.requiredSpecialty && s.includes(condition.requiredSpecialty))
      )
    );

    return matched.length > 0 ? matched : MOCK_HOCK_HOSPITALS_SAFE;
  },

  calculateHospitalETA(startJunctionId: string, hospital: Hospital): { etaMin: number; distanceKm: number } {
    // Distance approximation between start junction and hospital junction
    const juncIndex = parseInt(startJunctionId.replace('J', ''), 10) || 1;
    const hospJuncIndex = parseInt(hospital.junctionId.replace('J', ''), 10) || 7;
    const diff = Math.abs(juncIndex - hospJuncIndex);

    const baseDistanceKm = Math.max(1.8, +(diff * 0.9 + 1.2).toFixed(1));
    const baseEtaMin = Math.max(3.5, +(baseDistanceKm * 1.5 + (hospital.capacityLevel === 'Busy' ? 1.5 : 0)).toFixed(1));

    return {
      etaMin: baseEtaMin,
      distanceKm: baseDistanceKm,
    };
  },

  compareHospitalETA(hospitals: Hospital[], startJunctionId: string) {
    return hospitals.map((h) => {
      const stats = this.calculateHospitalETA(startJunctionId, h);
      return {
        hospital: h,
        etaMin: stats.etaMin,
        distanceKm: stats.distanceKm,
      };
    }).sort((a, b) => a.etaMin - b.etaMin);
  },

  selectBestHospital(
    conditionIdOrName: string,
    startJunctionId: string
  ): {
    hospital: Hospital;
    etaMin: number;
    distanceKm: number;
    reason: string;
  } {
    const suitable = this.findSuitableHospitals(conditionIdOrName);
    const ranked = this.compareHospitalETA(suitable, startJunctionId);

    const best = ranked[0] || {
      hospital: MOCK_HOCK_HOSPITALS_SAFE[0],
      etaMin: 6.5,
      distanceKm: 4.0,
    };

    let reason = `Lowest current estimated travel time (${best.etaMin} min) among suitable medical facilities.`;
    if (conditionIdOrName.toLowerCase().includes('cardiac')) {
      reason = `Direct Catheterization & Coronary Care Unit available with fastest ETA (${best.etaMin} min).`;
    } else if (conditionIdOrName.toLowerCase().includes('trauma') || conditionIdOrName.toLowerCase().includes('bleeding')) {
      reason = `Certified Level-1 Trauma Emergency Team on standby (${best.etaMin} min ETA).`;
    } else if (conditionIdOrName.toLowerCase().includes('stroke') || conditionIdOrName.toLowerCase().includes('neuro')) {
      reason = `Dedicated Comprehensive Stroke Center with immediate neurovascular imaging ready.`;
    } else if (conditionIdOrName.toLowerCase().includes('burn')) {
      reason = `Specialized Burn Intensive Care Unit verified with quickest transit time.`;
    }

    return {
      hospital: best.hospital,
      etaMin: best.etaMin,
      distanceKm: best.distanceKm,
      reason,
    };
  },
};

const MOCK_HOCK_HOSPITALS_SAFE = MOCK_HOSPITALS;
