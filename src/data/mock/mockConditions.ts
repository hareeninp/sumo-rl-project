import { WeatherData } from '../../types';

export const MOCK_WEATHER: WeatherData = {
  condition: 'Light Rain',
  temperatureC: 17,
  visibilityKm: 8.5,
  rainIntensity: 'light',
  affectedRoadIds: ['R2', 'R10'],
  advisory: 'Wet pavement along Pine Expressway and Harbor Link. Speeds adjusted for traction safety.',
};

export const MOCK_ROAD_CONDITIONS = [
  {
    roadId: 'R7',
    name: 'Tech Center Bypass',
    condition: 'construction',
    delayMin: 3,
    description: 'Active utility excavation - right lane reduced',
  },
  {
    roadId: 'R2',
    name: 'Pine Expressway',
    condition: 'moderate_traffic',
    delayMin: 4,
    description: 'High commuter density approaching J3',
  },
];
