import {
  RouteOption,
  TurnInstruction,
  Road,
} from '../types';

import {
  MOCK_JUNCTIONS,
} from '../data/mock/mockJunctions';

import {
  MOCK_ROADS,
} from '../data/mock/mockRoads';


class NavigationService {

  private isNavigating = false;

  private voiceEnabled = true;

  private lastSpokenInstructionId = '';


  // ==========================================================
  // NAVIGATION CONTROL
  // ==========================================================

  public startNavigation(): boolean {

    this.isNavigating = true;

    this.lastSpokenInstructionId = '';

    return true;

  }


  public endNavigation(): boolean {

    this.isNavigating = false;

    this.stopSpeech();

    return false;

  }


  public isNavigationActive(): boolean {

    return this.isNavigating;

  }


  // ==========================================================
  // VOICE CONTROL
  // ==========================================================

  public toggleVoice(
    enabled?: boolean
  ): boolean {

    this.voiceEnabled =
      enabled !== undefined
        ? enabled
        : !this.voiceEnabled;

    if (!this.voiceEnabled) {
      this.stopSpeech();
    }

    return this.voiceEnabled;

  }


  public isVoiceEnabled(): boolean {

    return this.voiceEnabled;

  }


  // ==========================================================
  // GENERATE TURN INSTRUCTIONS
  // ==========================================================

  public generateTurnInstructions(
    route: RouteOption
  ): TurnInstruction[] {

    const path =
      route.pathJunctionIds;

    const instructions:
      TurnInstruction[] = [];


    // --------------------------------------------------------
    // No route
    // --------------------------------------------------------

    if (
      !path ||
      path.length === 0
    ) {

      return [
        {
          id: 'inst-default',

          instruction:
            'Proceed to emergency destination',

          maneuver: 'straight',

          distanceMeters: 400,

          junctionId: 'J1',

          roadName:
            'Emergency Corridor',
        },
      ];

    }


    // --------------------------------------------------------
    // Single junction
    // --------------------------------------------------------

    if (path.length === 1) {

      const junction =
        MOCK_JUNCTIONS.find(
          j => j.id === path[0]
        );

      return [
        {
          id: `inst-arrive-${path[0]}`,

          instruction:
            `Proceed to ${
              junction?.name ||
              'destination'
            }`,

          maneuver: 'arrive',

          distanceMeters: 100,

          junctionId: path[0],

          roadName:
            'Emergency Access',
        },
      ];

    }


    // --------------------------------------------------------
    // Build instructions
    // --------------------------------------------------------

    for (
      let i = 0;
      i < path.length - 1;
      i++
    ) {

      const currentId =
        path[i];

      const nextId =
        path[i + 1];


      const currentJunction =
        MOCK_JUNCTIONS.find(
          j => j.id === currentId
        );

      const nextJunction =
        MOCK_JUNCTIONS.find(
          j => j.id === nextId
        );


      const road =
        MOCK_ROADS.find(
          r =>
            (
              r.fromJunction === currentId &&
              r.toJunction === nextId
            ) ||
            (
              r.fromJunction === nextId &&
              r.toJunction === currentId
            )
        );


      const roadName =
        road?.name ||
        `Emergency Corridor`;


      const roadLengthKm =
  road &&
  'lengthKm' in road
    ? Number(
        (road as Road & {
          lengthKm?: number;
        }).lengthKm ?? 1
      )
    : 1;

      const distanceMeters =
        Math.max(
          100,
          Math.round(
            roadLengthKm * 1000
          )
        );


      let maneuver:
        TurnInstruction['maneuver'] =
          'straight';

      let instruction =
        `Continue straight onto ${roadName}`;


      // ------------------------------------------------------
      // FIRST SEGMENT
      // ------------------------------------------------------

      if (i === 0) {

        maneuver = 'straight';

        instruction =
          `Proceed onto ${roadName}`;

      }


      // ------------------------------------------------------
      // FINAL SEGMENT
      // ------------------------------------------------------

      else if (
        i === path.length - 2
      ) {

        maneuver = 'arrive';

        instruction =
          `Approaching ${
            nextJunction?.name ||
            'your destination'
          }`;

      }


      // ------------------------------------------------------
      // INTERMEDIATE SEGMENTS
      // ------------------------------------------------------

      else {

        /*
         * The old implementation randomly alternated
         * directions using i % 2.
         *
         * That creates unrealistic navigation.
         *
         * For now we use deterministic instructions
         * without pretending to know the exact geometry.
         */

        const direction =
          this.getDeterministicDirection(i);

        maneuver = direction.maneuver;

        instruction =
          `${direction.text} at ${
            currentJunction?.name ||
            currentId
          } onto ${roadName}`;

      }


      instructions.push({

        id:
          `inst-${i}-${currentId}-${nextId}`,

        instruction,

        maneuver,

        distanceMeters,

        junctionId: nextId,

        roadName,

      });

    }


    // --------------------------------------------------------
    // FINAL ARRIVAL
    // --------------------------------------------------------

    const finalId =
      path[path.length - 1];

    const finalJunction =
      MOCK_JUNCTIONS.find(
        j => j.id === finalId
      );


    instructions.push({

      id:
        `inst-arrive-${finalId}`,

      instruction:
        `Arrive at ${
          finalJunction?.name ||
          'your destination'
        }`,

      maneuver: 'arrive',

      distanceMeters: 50,

      junctionId: finalId,

      roadName:
        'Emergency Bay Access',

    });


    return instructions;

  }


  // ==========================================================
  // DETERMINISTIC DIRECTION
  // ==========================================================

  private getDeterministicDirection(
    index: number
  ): {
    maneuver:
      | 'turn_right'
      | 'turn_left'
      | 'slight_right'
      | 'slight_left';

    text: string;
  } {

    const directions = [

      {
        maneuver:
          'turn_left' as const,

        text:
          'Turn left',
      },

      {
        maneuver:
          'turn_right' as const,

        text:
          'Turn right',
      },

      {
        maneuver:
          'slight_left' as const,

        text:
          'Keep left',
      },

      {
        maneuver:
          'slight_right' as const,

        text:
          'Keep right',
      },

    ];


    return directions[
      index % directions.length
    ];

  }


  // ==========================================================
  // NEXT INSTRUCTION
  // ==========================================================

  public getNextInstruction(
    route: RouteOption,
    progressPercent: number
  ): TurnInstruction {
    const instructions = this.generateTurnInstructions(route);

    if (instructions.length === 0) {
      return {
        id: 'default',
        instruction: 'Proceed to emergency destination',
        maneuver: 'straight',
        distanceMeters: 400,
        junctionId: 'J1',
        roadName: 'Emergency Corridor',
      };
    }

    const progress = Math.max(0, Math.min(100, progressPercent));

    // If reached destination (100% progress)
    if (progress >= 100) {
      const last = instructions[instructions.length - 1];
      return {
        ...last,
        distanceMeters: 0,
      };
    }

    // Number of active road legs (excluding final arrival note)
    const legCount = Math.max(1, instructions.length - 1);

    // Compute total distance across legs
    let totalMeters = 0;
    for (let i = 0; i < legCount; i++) {
      totalMeters += Math.max(100, instructions[i].distanceMeters);
    }

    const travelledMeters = (progress / 100) * totalMeters;
    let accumulatedMeters = 0;
    let activeIndex = 0;
    let remainingMeters = 0;

    for (let i = 0; i < legCount; i++) {
      const segMeters = Math.max(100, instructions[i].distanceMeters);
      const segEnd = accumulatedMeters + segMeters;

      if (travelledMeters < segEnd || i === legCount - 1) {
        activeIndex = i;
        remainingMeters = Math.max(0, Math.round(segEnd - travelledMeters));
        break;
      }
      accumulatedMeters += segMeters;
    }

    const active = instructions[activeIndex];
    const result: TurnInstruction = {
      ...active,
      distanceMeters: remainingMeters,
    };


    // --------------------------------------------------------
    // Voice announcement
    // --------------------------------------------------------

    if (
      this.voiceEnabled &&
      this.isNavigating &&
      this.lastSpokenInstructionId !==
        result.id
    ) {

      this.lastSpokenInstructionId =
        result.id;

      this.speakInstruction(
        `In ${result.distanceMeters} meters, ${result.instruction}`
      );

    }


    return result;

  }


  // ==========================================================
  // REMAINING DISTANCE
  // ==========================================================

  public getRemainingDistance(
    route: RouteOption,
    progressPercent: number
  ): number {

    const progress =
      Math.max(
        0,
        Math.min(
          100,
          progressPercent
        )
      );


    const remaining =
      route.totalDistanceKm *
      (
        1 -
        progress / 100
      );


    return Math.max(
      0.1,
      +remaining.toFixed(1)
    );

  }


  // ==========================================================
  // REMAINING ETA
  // ==========================================================

  public getRemainingETA(
    route: RouteOption,
    progressPercent: number
  ): number {

    const progress =
      Math.max(
        0,
        Math.min(
          100,
          progressPercent
        )
      );


    const remaining =
      route.etaMinutes *
      (
        1 -
        progress / 100
      );


    return Math.max(
      0.2,
      +remaining.toFixed(1)
    );

  }


  // ==========================================================
  // TEXT TO SPEECH
  // ==========================================================

  public speakInstruction(
    text: string
  ): void {

    if (
      !this.voiceEnabled ||
      typeof window === 'undefined' ||
      !window.speechSynthesis
    ) {

      return;

    }


    try {

      window.speechSynthesis.cancel();


      const utterance =
        new SpeechSynthesisUtterance(
          text
        );


      utterance.rate = 1.05;

      utterance.pitch = 1.0;

      utterance.volume = 0.9;


      window.speechSynthesis.speak(
        utterance
      );

    } catch {

      // Ignore browser speech errors

    }

  }


  // ==========================================================
  // STOP SPEECH
  // ==========================================================

  public stopSpeech(): void {

    if (
      typeof window !== 'undefined' &&
      window.speechSynthesis
    ) {

      try {

        window.speechSynthesis.cancel();

      } catch {

        // Ignore browser speech errors

      }

    }

  }

}


// ============================================================
// SINGLETON
// ============================================================

export const navigationService =
  new NavigationService();