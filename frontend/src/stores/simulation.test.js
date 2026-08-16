/**
 * Wiring test: the store judges a death certificate from DECLARED meter metadata, not from a
 * hardcoded [0,1] range or a meter's name.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSimulationStore } from './simulation'

const METERS = [
  { name: 'energy', index: 0, bounds: { min: 0, max: 1 }, lethal_min: true, lethal_max: false, cascades_to: [], cascades_from: [] },
  { name: 'money', index: 1, bounds: { min: 0, max: 999999 }, lethal_min: false, lethal_max: false, cascades_to: [], cascades_from: [] },
  { name: 'heat', index: 2, bounds: { min: 0, max: 10 }, lethal_min: false, lethal_max: true, cascades_to: [], cascades_from: [] },
]

function connect(store, presentation = null) {
  store.handleMessage({ type: 'connected', meters: METERS, presentation })
}

describe('death certificate meters come from declared metadata', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('lists only meters near a declared lethal bound, formatted honestly', () => {
    const store = useSimulationStore()
    connect(store)
    store.handleMessage({
      type: 'episode_end', episode: 1, steps: 40, total_reward: 1.5, affordance_stats: [],
      final_meters: { energy: 0.05, money: 22.5, heat: 9.2 },
    })
    const cert = store.deathCertificates[0]
    const byName = Object.fromEntries(cert.criticalMeters.map(m => [m.name, m]))
    expect(byName.money).toBeUndefined() // no lethal bound → never "critical", whatever its magnitude
    expect(byName.energy.severity).toBe('critical')
    expect(byName.energy.display).toBe('0.05') // not "5%"
    expect(byName.heat.severity).toBe('critical') // near its lethal MAX
    expect(byName.heat.display).toBe('9.2')
    expect(cert.criticalMeters.map(m => m.name)).toEqual(['energy', 'heat']) // closest to a lethal bound first
    expect(JSON.stringify(cert)).not.toMatch(/[%$]/)
  })

  it('applies a declared presentation to the certificate display', () => {
    const store = useSimulationStore()
    connect(store, { meters: { energy: { label: 'Vigour', format: { kind: 'percent', decimals: 0 }, color: '#0f0' } }, affordances: {} })
    store.handleMessage({
      type: 'episode_end', episode: 2, steps: 4, total_reward: 0, affordance_stats: [],
      final_meters: { energy: 0.25 },
    })
    const m = store.deathCertificates[0].criticalMeters[0]
    expect(m.label).toBe('Vigour')
    expect(m.severity).toBe('low')
    expect(m.display).toBe('25%')
  })

  it('renders nothing for meters the server did not describe', () => {
    const store = useSimulationStore()
    store.handleMessage({ type: 'connected', meters: [], presentation: null })
    store.handleMessage({ type: 'episode_end', episode: 3, steps: 1, total_reward: 0, affordance_stats: [], final_meters: { energy: 0.0 } })
    expect(store.deathCertificates[0].criticalMeters).toEqual([])
  })
})
