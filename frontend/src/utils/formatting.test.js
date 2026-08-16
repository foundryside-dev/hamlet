import { describe, it, expect } from 'vitest'
import {
  getMeterFraction,
  getMeterPercentage,
  formatMeterValue,
  isMeterCritical,
  meterLabel,
  affordanceIcon,
  affordanceGlyph,
  nameGlyph,
  cascadeText,
  capitalize
} from './formatting'

const UNIT = { min: 0, max: 1 }
const MONEY_BOUNDS = { min: 0, max: 999999 }

describe('getMeterFraction / getMeterPercentage', () => {
  it('maps a value onto its declared range', () => {
    expect(getMeterFraction(0.85, UNIT)).toBeCloseTo(0.85)
    expect(getMeterPercentage(0.85, UNIT)).toBeCloseTo(85)
    expect(getMeterFraction(50, { min: 0, max: 200 })).toBeCloseTo(0.25)
    expect(getMeterFraction(0, { min: -1, max: 1 })).toBeCloseTo(0.5)
  })

  it('does not peg a wide-range meter — money 22.5 in [0, 999999] is ~0.00225%', () => {
    const pct = getMeterPercentage(22.5, MONEY_BOUNDS)
    expect(pct).toBeCloseTo(0.00225, 5)
    expect(pct).toBeLessThan(1)
    expect(pct).not.toBe(100)
  })

  it('clamps to [0, 1] / [0, 100]', () => {
    expect(getMeterFraction(1.5, UNIT)).toBe(1)
    expect(getMeterFraction(-0.5, UNIT)).toBe(0)
    expect(getMeterPercentage(7, UNIT)).toBe(100)
  })

  it('handles a degenerate range without dividing by zero', () => {
    expect(getMeterFraction(3, { min: 3, max: 3 })).toBe(0)
  })
})

describe('formatMeterValue — honest default (no presentation entry)', () => {
  it('renders energy 0.85 in [0, 1] as "0.85" — no percent sign', () => {
    expect(formatMeterValue(0.85, UNIT, null)).toBe('0.85')
  })

  it('renders money 22.5 in [0, 999999] as the raw value, never "$2250"', () => {
    const shown = formatMeterValue(22.5, MONEY_BOUNDS, null)
    expect(shown).toBe('23')
    expect(shown).not.toContain('$')
    expect(shown).not.toContain('%')
    expect(shown).not.toBe('$2250')
  })

  it('derives precision from the declared range', () => {
    expect(formatMeterValue(0.5, { min: 0, max: 1 }, null)).toBe('0.50')
    expect(formatMeterValue(42.25, { min: 0, max: 100 }, null)).toBe('42.3')
    expect(formatMeterValue(1234.5, { min: 0, max: 5000 }, null)).toBe('1235')
  })

  it('never emits $ or % by default, whatever the range', () => {
    for (const bounds of [UNIT, { min: 0, max: 100 }, MONEY_BOUNDS]) {
      const s = formatMeterValue(0.5, bounds, null)
      expect(s).not.toMatch(/[$%]/)
    }
    expect(formatMeterValue(0.5, UNIT, undefined)).not.toMatch(/[$%]/)
  })
})

describe('formatMeterValue — declared presentation formats', () => {
  it('currency: symbol + raw value at declared decimals', () => {
    const entry = { label: 'Money', format: { kind: 'currency', symbol: '$', decimals: 0 }, color: '#fbbf24' }
    expect(formatMeterValue(22.5, MONEY_BOUNDS, entry)).toBe('$23')
    const twoDp = { ...entry, format: { kind: 'currency', symbol: '€', decimals: 2 } }
    expect(formatMeterValue(22.5, MONEY_BOUNDS, twoDp)).toBe('€22.50')
  })

  it('percent: percentage of the declared range', () => {
    const entry = { label: 'Energy', format: { kind: 'percent', decimals: 0 }, color: '#10b981' }
    expect(formatMeterValue(0.85, UNIT, entry)).toBe('85%')
    expect(formatMeterValue(50, { min: 0, max: 200 }, entry)).toBe('25%')
    const oneDp = { ...entry, format: { kind: 'percent', decimals: 1 } }
    expect(formatMeterValue(0.856, UNIT, oneDp)).toBe('85.6%')
  })

  it('plain: raw value at declared decimals', () => {
    const entry = { label: 'X', format: { kind: 'plain', decimals: 3 }, color: '#fff' }
    expect(formatMeterValue(0.85, UNIT, entry)).toBe('0.850')
    expect(formatMeterValue(22.5, MONEY_BOUNDS, { ...entry, format: { kind: 'plain', decimals: 1 } })).toBe('22.5')
  })

  it('rejects an unknown format kind loudly rather than guessing', () => {
    const entry = { label: 'X', format: { kind: 'hex', decimals: 0 }, color: '#fff' }
    expect(() => formatMeterValue(1, UNIT, entry)).toThrow()
  })
})

describe('isMeterCritical', () => {
  const lethalMin = { name: 'a', bounds: UNIT, lethal_min: true, lethal_max: false }
  const lethalMax = { name: 'b', bounds: UNIT, lethal_min: false, lethal_max: true }
  const notLethal = { name: 'c', bounds: MONEY_BOUNDS, lethal_min: false, lethal_max: false }

  it('lethal_min: critical when within 20% of the min bound', () => {
    expect(isMeterCritical(0.1, lethalMin)).toBe(true)
    expect(isMeterCritical(0.19, lethalMin)).toBe(true)
    expect(isMeterCritical(0.2, lethalMin)).toBe(false)
    expect(isMeterCritical(0.9, lethalMin)).toBe(false)
  })

  it('lethal_max: critical when within 20% of the max bound', () => {
    expect(isMeterCritical(0.9, lethalMax)).toBe(true)
    expect(isMeterCritical(0.81, lethalMax)).toBe(true)
    expect(isMeterCritical(0.8, lethalMax)).toBe(false)
    expect(isMeterCritical(0.1, lethalMax)).toBe(false)
  })

  it('no lethal bound: never critical, however low', () => {
    expect(isMeterCritical(0, notLethal)).toBe(false)
    expect(isMeterCritical(22.5, notLethal)).toBe(false)
    expect(isMeterCritical(999999, notLethal)).toBe(false)
  })

  it('uses the declared range, not a [0,1] assumption', () => {
    const wide = { name: 'w', bounds: { min: 0, max: 200 }, lethal_min: true, lethal_max: false }
    expect(isMeterCritical(30, wide)).toBe(true)   // 15%
    expect(isMeterCritical(50, wide)).toBe(false)  // 25%
  })

  it('missing metadata is never critical', () => {
    expect(isMeterCritical(0, null)).toBe(false)
    expect(isMeterCritical(0, undefined)).toBe(false)
  })
})

describe('meterLabel', () => {
  it('uses the declared label when present, else a capitalised name', () => {
    expect(meterLabel('money', { label: 'Cash', format: { kind: 'plain', decimals: 0 }, color: '#fff' })).toBe('Cash')
    expect(meterLabel('money', null)).toBe('Money')
    expect(meterLabel('drink_water', undefined)).toBe('Drink_water')
  })
})

describe('nameGlyph / affordanceGlyph / affordanceIcon', () => {
  const presentation = {
    meters: {},
    affordances: { EAT: { label: 'Eat', icon: '🍽️' } }
  }

  it('nameGlyph is deterministic and derived only from the name', () => {
    expect(nameGlyph('DRINK_WATER')).toBe('DW')
    expect(nameGlyph('EAT')).toBe('EA')
    expect(nameGlyph('CLEAN_HOUSE')).toBe('CH')
    expect(nameGlyph('brush teeth')).toBe('BT')
    expect(nameGlyph('a_b_c_d')).toBe('ABC')
    expect(nameGlyph('X')).toBe('X')
    expect(nameGlyph('')).toBe('')
    expect(nameGlyph('DRINK_WATER')).toBe(nameGlyph('DRINK_WATER'))
  })

  it('affordanceIcon prefers the payload icon, then the declared one, else null', () => {
    expect(affordanceIcon('EAT', presentation, '🥣')).toBe('🥣')
    expect(affordanceIcon('EAT', presentation, null)).toBe('🍽️')
    expect(affordanceIcon('EAT', presentation, undefined)).toBe('🍽️')
    expect(affordanceIcon('SLEEP', presentation, null)).toBeNull()
    expect(affordanceIcon('EAT', null, null)).toBeNull()
    expect(affordanceIcon('EAT', undefined)).toBeNull()
  })

  it('affordanceGlyph is the declared icon, else the name-derived abbreviation — never a table', () => {
    expect(affordanceGlyph('EAT', presentation, null)).toBe('🍽️')
    expect(affordanceGlyph('SLEEP', presentation, null)).toBe('SL')
    expect(affordanceGlyph('DRINK_WATER', null, null)).toBe('DW')
    expect(affordanceGlyph('WORK', null, '💼')).toBe('💼')
  })
})

describe('cascadeText', () => {
  const metaByName = {
    hygiene: { name: 'hygiene', bounds: UNIT, lethal_min: false, lethal_max: false, cascades_to: ['satiation', 'mood'], cascades_from: [] },
    satiation: { name: 'satiation', bounds: UNIT, lethal_min: false, lethal_max: false, cascades_to: [], cascades_from: ['hygiene'] },
    mood: { name: 'mood', bounds: UNIT, lethal_min: false, lethal_max: false, cascades_to: [], cascades_from: ['hygiene'] }
  }

  it('lists declared cascade targets with their labels', () => {
    expect(cascadeText(metaByName.hygiene, metaByName, null)).toBe('→ Satiation + Mood')
  })

  it('uses declared labels when presentation provides them', () => {
    const presentation = { meters: { mood: { label: 'Spirits', format: { kind: 'plain', decimals: 2 }, color: '#fff' } }, affordances: {} }
    expect(cascadeText(metaByName.hygiene, metaByName, presentation)).toBe('→ Satiation + Spirits')
  })

  it('is empty when the meter cascades into nothing', () => {
    expect(cascadeText(metaByName.satiation, metaByName, null)).toBe('')
    expect(cascadeText(null, metaByName, null)).toBe('')
  })
})

describe('capitalize (unchanged)', () => {
  it('capitalises the first letter', () => {
    expect(capitalize('energy')).toBe('Energy')
    expect(capitalize('')).toBe('')
  })
})
