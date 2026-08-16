import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MeterPanel from './MeterPanel.vue'

// Two declared meters, in compiled index order: a wide-range non-lethal one first, then a
// unit-range lethal one. Names are deliberately arbitrary — nothing may key on them.
const meterMetadata = [
  { name: 'coins', index: 0, bounds: { min: 0, max: 999999 }, lethal_min: false, lethal_max: false, cascades_to: [], cascades_from: [] },
  { name: 'vigor', index: 1, bounds: { min: 0, max: 1 }, lethal_min: true, lethal_max: false, cascades_to: ['coins'], cascades_from: [] }
]

const agentMeters = { agent_0: { meters: { vigor: 0.1, coins: 22.5 } } }

function mountPanel(presentation = null, meters = agentMeters) {
  return mount(MeterPanel, {
    props: { agentMeters: meters, meterMetadata, presentation, lifetimeProgress: 0.25, agentAge: 48 }
  })
}

describe('MeterPanel', () => {
  it('renders meters as one flat list in compiled order, not object-key order', () => {
    const wrapper = mountPanel()
    const rows = wrapper.findAll('[data-meter]')
    const names = rows.map(r => r.attributes('data-meter'))
    // agentMeters lists vigor before coins; compiled order says coins first.
    expect(names.slice(0, 2)).toEqual(['coins', 'vigor'])
    // Age bar is still present, after the declared meters.
    expect(names[2]).toBe('age')
  })

  it('with presentation null shows honest raw values — no $ or % anywhere', () => {
    const wrapper = mountPanel(null)
    const text = wrapper.text()
    expect(text).not.toContain('$')
    expect(text).not.toContain('%')
    expect(wrapper.find('[data-meter="coins"] .meter-value').text()).toBe('23')
    expect(wrapper.find('[data-meter="vigor"] .meter-value').text()).toBe('0.10')
  })

  it('bar width and aria-valuenow are the percentage of the declared range', () => {
    const wrapper = mountPanel()
    const coinsBar = wrapper.find('[data-meter="coins"] [role="progressbar"]')
    const coinsPct = Number(coinsBar.attributes('aria-valuenow'))
    expect(coinsPct).toBeLessThan(1)          // 22.5 / 999999 — not pegged
    expect(coinsPct).toBeGreaterThan(0)
    const vigorBar = wrapper.find('[data-meter="vigor"] [role="progressbar"]')
    expect(Number(vigorBar.attributes('aria-valuenow'))).toBeCloseTo(10)
    expect(vigorBar.attributes('style')).toContain('width: 10%')
  })

  it('shows $ only when a currency presentation is declared for the meter', () => {
    const presentation = {
      meters: { coins: { label: 'Cash', format: { kind: 'currency', symbol: '$', decimals: 0 }, color: '#fbbf24' } },
      affordances: {}
    }
    const wrapper = mountPanel(presentation)
    const coins = wrapper.find('[data-meter="coins"]')
    expect(coins.find('.meter-value').text()).toBe('$23')
    expect(coins.find('.meter-name').text()).toBe('Cash')
    // jsdom normalises hex colours to rgb(); #fbbf24 === rgb(251, 191, 36)
    expect(coins.find('[role="progressbar"]').attributes('style')).toMatch(/#fbbf24|rgb\(251, 191, 36\)/)
    // The undeclared meter stays honest.
    expect(wrapper.find('[data-meter="vigor"] .meter-value').text()).toBe('0.10')
  })

  it('marks lethal bounds and critical state from declarations only', () => {
    const wrapper = mountPanel()
    const vigor = wrapper.find('[data-meter="vigor"]')
    expect(vigor.classes()).toContain('critical')
    expect(vigor.find('.meter-lethal').exists()).toBe(true)
    expect(vigor.find('.meter-lethal').text()).toContain('min')
    const coins = wrapper.find('[data-meter="coins"]')
    expect(coins.classes()).not.toContain('critical')
    expect(coins.find('.meter-lethal').exists()).toBe(false)
  })

  it('renders cascade text from declared cascades_to', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('[data-meter="vigor"] .meter-relationship').text()).toBe('→ Coins')
    expect(wrapper.find('[data-meter="coins"] .meter-relationship').exists()).toBe(false)
  })

  it('skips declared meters absent from the agent payload', () => {
    const wrapper = mountPanel(null, { agent_0: { meters: { vigor: 0.5 } } })
    const names = wrapper.findAll('[data-meter]').map(r => r.attributes('data-meter'))
    expect(names).toEqual(['vigor', 'age'])
  })

  it('renders no meter rows when the server sent no metadata', () => {
    const wrapper = mount(MeterPanel, {
      props: { agentMeters, meterMetadata: [], presentation: null, lifetimeProgress: 0, agentAge: 0 }
    })
    const names = wrapper.findAll('[data-meter]').map(r => r.attributes('data-meter'))
    expect(names).not.toContain('coins')
    expect(names).not.toContain('vigor')
  })

  it('does not special-case any meter name in the rendered markup', () => {
    // Render with a completely different vocabulary and assert output shape is identical.
    const alt = [
      { name: 'zeta', index: 0, bounds: { min: 0, max: 999999 }, lethal_min: false, lethal_max: false, cascades_to: [], cascades_from: [] },
      { name: 'omega', index: 1, bounds: { min: 0, max: 1 }, lethal_min: true, lethal_max: false, cascades_to: ['zeta'], cascades_from: [] }
    ]
    const a = mountPanel().html().replace(/coins/g, 'N1').replace(/Coins/g, 'N1c').replace(/vigor/g, 'N2').replace(/Vigor/g, 'N2c')
    const b = mount(MeterPanel, {
      props: { agentMeters: { agent_0: { meters: { omega: 0.1, zeta: 22.5 } } }, meterMetadata: alt, presentation: null, lifetimeProgress: 0.25, agentAge: 48 }
    }).html().replace(/zeta/g, 'N1').replace(/Zeta/g, 'N1c').replace(/omega/g, 'N2').replace(/Omega/g, 'N2c')
    expect(b).toBe(a)
  })
})
