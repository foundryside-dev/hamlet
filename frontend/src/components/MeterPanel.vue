<template>
  <!-- ✅ Semantic HTML: section instead of div -->
  <section class="meter-panel" aria-labelledby="meter-heading">
    <div class="panel-header">
      <h3 id="meter-heading">Agent Meters</h3>
    </div>

    <!--
      One flat list in compiled index order (PDR-0025). Every rendering decision below comes
      from the meter's declared metadata or the pack's declared presentation — never from
      the meter's name.
    -->
    <div v-if="meters" class="meters" role="list">
      <template v-for="row in rows" :key="row.name">
        <div
          class="meter"
          role="listitem"
          :data-meter="row.name"
          :class="{ critical: row.critical }"
          :aria-label="`${row.label}: ${row.display}`"
        >
          <div class="meter-header">
            <span class="meter-name">{{ row.label }}</span>
            <span class="meter-value" aria-live="polite" aria-atomic="true" role="status">
              {{ row.display }}
            </span>
          </div>
          <div v-if="row.lethal || row.cascade" class="meter-notes">
            <span
              v-if="row.lethal"
              class="meter-lethal"
              :title="`Lethal at ${row.lethal} of declared range`"
            >⚠ lethal at {{ row.lethal }}</span>
            <span v-if="row.cascade" class="meter-relationship">{{ row.cascade }}</span>
          </div>
          <div class="meter-bar-container">
            <div
              class="meter-bar"
              role="progressbar"
              :aria-valuenow="row.percentage"
              aria-valuemin="0"
              aria-valuemax="100"
              :style="{
                width: row.percentage + '%',
                background: row.color
              }"
            ></div>
          </div>
        </div>
      </template>

      <!-- Age meter (progress to retirement) -->
      <div class="meter" role="listitem" data-meter="age">
        <div class="meter-header">
          <span class="meter-name">Age</span>
          <span class="meter-value" aria-live="polite" aria-atomic="true" role="status">
            {{ (props.agentAge / 24).toFixed(1) }} days
          </span>
        </div>
        <div class="meter-bar-container">
          <div
            class="meter-bar age-bar"
            role="progressbar"
            :aria-valuenow="Math.round(props.lifetimeProgress * 100)"
            aria-valuemin="0"
            aria-valuemax="100"
            :style="{
              width: (props.lifetimeProgress * 100) + '%',
              background: getAgeColor(props.lifetimeProgress)
            }"
          ></div>
        </div>
      </div>
    </div>

    <!-- ✅ Empty state when no meter data available -->
    <EmptyState
      v-else
      icon="📊"
      title="No Agent Data"
      message="Connect to the simulation to see agent meters."
    />
  </section>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import {
  formatMeterValue,
  getMeterFraction,
  getMeterPercentage,
  isMeterCritical,
  meterLabel,
  cascadeText
} from '../utils/formatting'

// ✅ Props First: Receive data from parent instead of importing store
const props = defineProps({
  agentMeters: {
    type: Object,
    default: () => ({})
  },
  // Declared per-meter facts in compiled index order (from `connected.meters`).
  meterMetadata: {
    type: Array,
    default: () => []
  },
  // The pack's opt-in presentation.yaml as JSON, or null — the honest default.
  presentation: {
    type: Object,
    default: null
  },
  lifetimeProgress: {
    type: Number,
    default: 0
  },
  agentAge: {
    type: Number,
    default: 0
  }
})

const meters = computed(() => {
  const agent = props.agentMeters['agent_0']
  return agent ? agent.meters : null
})

const metaByName = computed(() => {
  const byName = {}
  for (const meta of props.meterMetadata) byName[meta.name] = meta
  return byName
})

function presentationEntry(name) {
  const declared = props.presentation && props.presentation.meters
  return declared && declared[name] ? declared[name] : null
}

// Generic fraction-based bar colour when no colour is declared. Coloured by distance from
// the lethal bound where there is one; a lethal_max-only meter reads "danger" at the top.
function defaultColor(fraction, meta) {
  const danger = meta.lethal_max && !meta.lethal_min ? 1 - fraction : fraction
  if (danger > 0.6) return 'var(--color-success)'
  if (danger > 0.3) return 'var(--color-warning)'
  return 'var(--color-error)'
}

function lethalMarker(meta) {
  if (meta.lethal_min && meta.lethal_max) return 'min and max'
  if (meta.lethal_min) return 'min'
  if (meta.lethal_max) return 'max'
  return null
}

// One row per declared meter present in the agent payload, in compiled order.
const rows = computed(() => {
  const values = meters.value
  if (!values) return []
  const out = []
  for (const meta of props.meterMetadata) {
    const value = values[meta.name]
    if (value === undefined) continue
    const entry = presentationEntry(meta.name)
    const fraction = getMeterFraction(value, meta.bounds)
    out.push({
      name: meta.name,
      label: meterLabel(meta.name, entry),
      display: formatMeterValue(value, meta.bounds, entry),
      percentage: getMeterPercentage(value, meta.bounds),
      color: entry ? entry.color : defaultColor(fraction, meta),
      critical: isMeterCritical(value, meta),
      lethal: lethalMarker(meta),
      cascade: cascadeText(meta, metaByName.value, props.presentation)
    })
  }
  return out
})

// Get color for age/retirement progress bar
function getAgeColor(progress) {
  // Green -> Yellow -> Red as agent ages
  if (progress < 0.5) return 'var(--color-success)' // young
  if (progress < 0.75) return 'var(--color-warning)' // middle age
  return 'var(--color-error)' // near retirement/death
}
</script>

<style scoped>
/* ✅ Refactored to use design tokens */
.meter-panel {
  background: var(--color-bg-secondary);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md) var(--spacing-lg) 2px var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.meter-panel h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.meters {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  flex: 1;
  overflow-y: auto;
}

.meter {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  position: relative;
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-base);
}

.meter-notes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  line-height: 1.2;
}

/* ===== Declared facts: lethal bound marker and cascade text ===== */
.meter-lethal {
  color: var(--color-error);
  font-weight: var(--font-weight-medium);
  padding: calc(var(--spacing-xs) / 2) var(--spacing-xs);
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--border-radius-sm);
  border-left: 2px solid var(--color-error);
}

.meter-relationship {
  color: var(--color-text-secondary);
  padding: calc(var(--spacing-xs) / 2) var(--spacing-xs);
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--border-radius-sm);
  border-left: 2px solid var(--color-info);
  font-weight: var(--font-weight-medium);
  opacity: 0.85;
}

.meter.critical {
  animation: pulse 1s ease-in-out infinite;
  will-change: transform, opacity;
  transform: translateZ(0);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.meter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meter-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.meter-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  font-family: 'Monaco', 'Courier New', monospace;
  font-variant-numeric: tabular-nums;
  min-width: 3ch;
  text-align: right;
}

.meter-bar-container {
  width: 100%;
  height: 20px;
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-full);
  overflow: hidden;
}

.meter-bar {
  height: 100%;
  border-radius: var(--border-radius-full);
  transition: width var(--transition-base), background var(--transition-base);
}

/* Respect user's reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
