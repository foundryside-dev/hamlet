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
