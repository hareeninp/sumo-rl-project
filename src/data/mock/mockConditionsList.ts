import { PatientCondition } from '../../types';

export const PATIENT_CONDITIONS: PatientCondition[] = [
  { id: 'cardiac', name: '❤️ Cardiac Emergency', icon: 'HeartPulse', isSpecialized: true, requiredSpecialty: 'Cardiac Emergency' },
  { id: 'stroke', name: '🧠 Stroke / Neurological Emergency', icon: 'Brain', isSpecialized: true, requiredSpecialty: 'Stroke / Neurological Emergency' },
  { id: 'trauma', name: '🚗 Road Accident / Major Trauma', icon: 'AlertTriangle', isSpecialized: true, requiredSpecialty: 'Road Accident / Major Trauma' },
  { id: 'bleeding', name: '🩸 Severe Bleeding', icon: 'Droplets', isSpecialized: true, requiredSpecialty: 'Severe Bleeding' },
  { id: 'breathing', name: '🫁 Breathing Difficulty', icon: 'Wind', isSpecialized: true, requiredSpecialty: 'Breathing Difficulty' },
  { id: 'head_injury', name: '🤕 Head Injury', icon: 'Activity', isSpecialized: true, requiredSpecialty: 'Head Injury' },
  { id: 'burns', name: '🔥 Burns', icon: 'Flame', isSpecialized: true, requiredSpecialty: 'Burns' },
  { id: 'fracture', name: '🦴 Fracture / Serious Injury', icon: 'Bone', isSpecialized: false },
  { id: 'poisoning', name: '☠️ Poisoning / Toxic Exposure', icon: 'Skull', isSpecialized: true, requiredSpecialty: 'Poisoning / Toxic Exposure' },
  { id: 'allergy', name: '⚠️ Severe Allergic Reaction', icon: 'ShieldAlert', isSpecialized: false },
  { id: 'seizure', name: '⚡ Seizure', icon: 'Zap', isSpecialized: true, requiredSpecialty: 'Seizure' },
  { id: 'abdominal', name: '🩺 Abdominal Emergency', icon: 'Stethoscope', isSpecialized: false },
  { id: 'pregnancy', name: '🤰 Pregnancy / Obstetric Emergency', icon: 'Baby', isSpecialized: true, requiredSpecialty: 'Pregnancy / Obstetric Emergency' },
  { id: 'unconscious', name: '🛌 Unconscious / Unresponsive', icon: 'Bed', isSpecialized: true, requiredSpecialty: 'Unconscious / Unresponsive' },
  { id: 'general', name: '🚑 General Emergency', icon: 'Ambulance', isSpecialized: false },
];
