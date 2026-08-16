/**
 * Formatting Utilities
 *
 * Reusable, pure formatting functions for consistent display.
 *
 * Presentation is DECLARED, honest by default, and never inferred from a variable's name
 * (PDR-0025). Nothing in this module takes a meter or affordance name to decide how a value
 * looks: every meter function is driven by the meter's declared metadata (`bounds`,
 * `lethal_min` / `lethal_max`, `cascades_to`, sent on the `connected` message) plus an
 * optional presentation entry from the pack's `presentation.yaml`. Absent a declaration, the
 * honest default renders the raw value against its declared range — no `%`, no `$`.
 */

/**
 * Capitalize the first letter of a string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Fraction of the declared range a value sits at.
 * @param {number} value - Raw meter value
 * @param {{min: number, max: number}} bounds - Declared bounds
 * @returns {number} clamp((value - min) / (max - min), 0, 1); 0 for a degenerate range
 */
export function getMeterFraction(value, bounds) {
  const range = bounds.max - bounds.min
  if (!(range > 0)) return 0
  const fraction = (value - bounds.min) / range
  return Math.max(0, Math.min(1, fraction))
}

/**
 * Percentage of the declared range a value sits at (for progress bars / aria-valuenow).
 * @param {number} value - Raw meter value
 * @param {{min: number, max: number}} bounds - Declared bounds
 * @returns {number} 0..100
 */
export function getMeterPercentage(value, bounds) {
  return getMeterFraction(value, bounds) * 100
}

/**
 * Decimal places for the honest default rendering, derived from the declared range:
 *   range <= 1   → 2 decimals  (e.g. 0.85)
 *   range <= 100 → 1 decimal   (e.g. 42.3)
 *   otherwise    → 0 decimals  (e.g. 23)
 * @param {{min: number, max: number}} bounds
 * @returns {number}
 */
function defaultDecimals(bounds) {
  const range = bounds.max - bounds.min
  if (range <= 1) return 2
  if (range <= 100) return 1
  return 0
}

/**
 * Format a meter value for display.
 *
 * With a declared presentation entry, its `format` is applied:
 *   - `plain`    → `value.toFixed(decimals)`
 *   - `percent`  → percentage of the declared range, `${pct.toFixed(decimals)}%`
 *   - `currency` → `${symbol}${value.toFixed(decimals)}`
 * Any other kind throws — the server validates the vocabulary, so a stray kind is a defect.
 *
 * Without one, the honest default: the raw value with precision from `defaultDecimals` (see
 * above). NEVER a `%` or a `$` — units are declared or they are absent.
 *
 * @param {number} value - Raw meter value
 * @param {{min: number, max: number}} bounds - Declared bounds
 * @param {{label: string, format: object, color: string}|null|undefined} entry - Declared presentation for this meter, if any
 * @returns {string}
 */
export function formatMeterValue(value, bounds, entry) {
  if (!entry) {
    return value.toFixed(defaultDecimals(bounds))
  }
  const format = entry.format
  switch (format.kind) {
    case 'plain':
      return value.toFixed(format.decimals)
    case 'percent':
      return `${getMeterPercentage(value, bounds).toFixed(format.decimals)}%`
    case 'currency':
      return `${format.symbol}${value.toFixed(format.decimals)}`
    default:
      throw new Error(`Unknown meter format kind: ${String(format.kind)}`)
  }
}

/** Fraction of the declared range within which a lethal bound counts as "critical". */
const CRITICAL_BAND = 0.2

/**
 * Whether a meter is critical: it has a lethal bound and the value is within 20% of the
 * declared range of that bound. A meter with no lethal bound is never critical.
 * @param {number} value - Raw meter value
 * @param {{bounds: {min:number,max:number}, lethal_min: boolean, lethal_max: boolean}|null|undefined} meta
 * @returns {boolean}
 */
export function isMeterCritical(value, meta) {
  if (!meta) return false
  const fraction = getMeterFraction(value, meta.bounds)
  if (meta.lethal_min && fraction < CRITICAL_BAND) return true
  if (meta.lethal_max && fraction > 1 - CRITICAL_BAND) return true
  return false
}

/**
 * Display label for a meter: the declared label, else the capitalised name.
 * @param {string} name
 * @param {{label: string}|null|undefined} entry
 * @returns {string}
 */
export function meterLabel(name, entry) {
  return entry ? entry.label : capitalize(name)
}

/**
 * Deterministic abbreviation derived only from a name — the honest fallback glyph when no
 * icon is declared. Rule: split on non-alphanumerics; two or more words → the first letter of
 * each of the first three words; one word → its first two characters. Upper-cased.
 *   DRINK_WATER → DW, CLEAN_HOUSE → CH, EAT → EA, a_b_c_d → ABC, X → X
 * @param {string} name
 * @returns {string}
 */
export function nameGlyph(name) {
  if (!name) return ''
  const words = String(name).split(/[^A-Za-z0-9]+/).filter(Boolean)
  if (words.length === 0) return ''
  if (words.length >= 2) {
    return words.slice(0, 3).map(w => w.charAt(0)).join('').toUpperCase()
  }
  return words[0].slice(0, 2).toUpperCase()
}

/**
 * The declared icon for an affordance, or null. The per-affordance icon in the state payload
 * wins (the server already resolved it); otherwise the presentation's affordance entry.
 * @param {string} type - Affordance name
 * @param {{affordances: Object}|null|undefined} presentation
 * @param {string|null|undefined} iconFromPayload
 * @returns {string|null}
 */
export function affordanceIcon(type, presentation, iconFromPayload) {
  if (iconFromPayload) return iconFromPayload
  const entry = presentation && presentation.affordances ? presentation.affordances[type] : undefined
  return entry && entry.icon ? entry.icon : null
}

/**
 * Glyph rendered for an affordance: the declared icon if any, else `nameGlyph(type)`.
 * Never a lookup table.
 * @param {string} type - Affordance name
 * @param {{affordances: Object}|null|undefined} presentation
 * @param {string|null|undefined} iconFromPayload
 * @returns {string}
 */
export function affordanceGlyph(type, presentation, iconFromPayload) {
  return affordanceIcon(type, presentation, iconFromPayload) ?? nameGlyph(type)
}

/**
 * Human-readable cascade line for a meter, from its declared `cascades_to`, e.g.
 * "→ Health + Energy". Empty string when the meter cascades into nothing.
 * @param {{cascades_to: string[]}|null|undefined} meta - This meter's metadata
 * @param {Object<string, object>} metaByName - All meter metadata keyed by name (unused for labels today, kept so callers can pass one map)
 * @param {{meters: Object}|null|undefined} presentation
 * @returns {string}
 */
export function cascadeText(meta, metaByName, presentation) {
  if (!meta || !meta.cascades_to || meta.cascades_to.length === 0) return ''
  const labels = meta.cascades_to.map(target => {
    const entry = presentation && presentation.meters ? presentation.meters[target] : undefined
    return meterLabel(target, entry)
  })
  return `→ ${labels.join(' + ')}`
}

/**
 * Format reward value with sign
 * @param {number} reward - Reward value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted reward with sign
 */
export function formatReward(reward, decimals = 1) {
  const formatted = reward.toFixed(decimals)
  return reward > 0 ? `+${formatted}` : formatted
}

/**
 * Format number with commas for readability
 * @param {number} num - Number to format
 * @returns {string} Formatted number with commas
 */
export function formatNumber(num) {
  return num.toLocaleString('en-US')
}

/**
 * Format training metric with appropriate precision
 * @param {number} value - Metric value
 * @param {string} type - Metric type ('reward', 'length', 'loss', 'epsilon')
 * @returns {string} Formatted metric
 */
export function formatTrainingMetric(value, type) {
  switch (type) {
    case 'reward':
      return value.toFixed(2)
    case 'length':
      return value.toFixed(1)
    case 'loss':
      return value.toFixed(4)
    case 'epsilon':
      return value.toFixed(3)
    default:
      return value.toString()
  }
}
