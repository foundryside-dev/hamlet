/**
 * Application Constants
 *
 * Centralized constants used across components
 */

// Grid rendering
export const CELL_SIZE = 100 // pixels per cell (8x8 grid = 800px total)

// Action display names (support both numeric and string keys)
export const ACTION_ICONS = {
  // Numeric mappings (from action space)
  0: '↑ Up',
  1: '↓ Down',
  2: '← Left',
  3: '→ Right',
  4: '⚡ Interact',
  // String mappings (legacy support)
  up: '↑ Up',
  down: '↓ Down',
  left: '← Left',
  right: '→ Right',
  interact: '⚡ Interact'
}

// Affordance display
export const AFFORDANCE_ICONS = {
  // Current v2.1 affordance ids (all-caps)
  EAT: '🍽️',
  SLEEP: '🛌',
  SHOWER: '🚿',
  EXERCISE: '💪',
  WORK: '💼',
  SOCIALIZE: '🗣️',
  MEDITATE: '🧘',
  DRINK_WATER: '💧',
  BRUSH_TEETH: '🪥',
  LAUNDRY: '🧺',
  COOK: '🍳',
  CLEAN_HOUSE: '🧹',
  ENTERTAINMENT: '🎮',
  DOCTOR: '⚕️',
  // Legacy camel-case ids
  Bed: '🛏️',
  LuxuryBed: '🛌',  // Luxury bed (tier 2 rest)
  Shower: '🚿',
  Fridge: '🥘',       // Main food source in current env
  HomeMeal: '🥘',    // Legacy support
  FastFood: '🍔',
  Job: '💼',         // Office work
  Labor: '🔨',       // Physical labor
  Recreation: '🎮',  // Mood restoration tier 1
  Therapist: '🧠',   // Mood restoration tier 2
  Bar: '🍺',
  Gym: '💪',          // Fitness builder
  Park: '🌳',        // Free generalist
  Doctor: '⚕️',       // Health restoration tier 1
  Hospital: '🏥'     // Health restoration tier 2
}

// Meter thresholds
export const METER_THRESHOLDS = {
  CRITICAL: 20,    // Below this = critical (red)
  LOW: 30,         // Below this = low (warning)
  MODERATE: 60,    // Below this = moderate
  HEALTHY: 80      // Above this = healthy (green)
}

// Mood meter thresholds (higher is better)
export const MOOD_THRESHOLDS = {
  LOW: 30,         // Below this = low mood (red)
  MODERATE: 60,    // Between LOW and MODERATE = warning
  HIGH: 80         // Above this = healthy mood
}
