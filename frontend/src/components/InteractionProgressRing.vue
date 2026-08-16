<template>
  <!-- Progress ring around agent during multi-tick interactions -->
  <svg
    v-if="isActive"
    :width="ringSize"
    :height="ringSize"
    :style="{
      position: 'absolute',
      left: `${x * cellSize - ringSize / 2 + cellSize / 2}px`,
      top: `${y * cellSize - ringSize / 2 + cellSize / 2}px`,
      pointerEvents: 'none',
      zIndex: 50,
    }"
    class="progress-ring"
  >
    <!-- Background circle (subtle) -->
    <circle
      :cx="ringSize / 2"
      :cy="ringSize / 2"
      :r="radius"
      fill="none"
      stroke="rgba(255, 255, 255, 0.2)"
      :stroke-width="strokeWidth"
    />

    <!-- Progress arc (colored and glowing) -->
    <circle
      :cx="ringSize / 2"
      :cy="ringSize / 2"
      :r="radius"
      fill="none"
      :stroke-width="strokeWidth"
      :stroke-dasharray="circumference"
      :stroke-dashoffset="dashOffset"
      stroke-linecap="round"
      class="progress-arc"
      :style="{
        stroke: progressColor,
        filter: `drop-shadow(0 0 ${glowIntensity}px ${progressColor})`,
      }"
    />

    <!-- Center pulse effect -->
    <circle
      :cx="ringSize / 2"
      :cy="ringSize / 2"
      :r="radius * 0.4"
      :style="{ fill: progressColor }"
      opacity="0.2"
      class="center-pulse"
    />

    <!-- Progress percentage text (optional, for large rings) -->
    <text
      v-if="ringSize >= 60"
      :x="ringSize / 2"
      :y="ringSize / 2"
      text-anchor="middle"
      dominant-baseline="middle"
      :font-size="ringSize * 0.2"
      :style="{ fill: progressColor }"
      font-weight="bold"
      font-family="Monaco, monospace"
      class="progress-text"
    >
      {{ Math.round(progressPercent) }}%
    </text>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // Agent position
  x: {
    type: Number,
    required: true
  },
  y: {
    type: Number,
    required: true
  },
  // Progress (0-1 normalized)
  progress: {
    type: Number,
    required: true,
    validator: (value) => value >= 0 && value <= 1
  },
  // Grid cell size
  cellSize: {
    type: Number,
    default: 75
  }
})

// Only show when there's active progress
const isActive = computed(() => props.progress > 0)

// Ring dimensions
const ringSize = computed(() => props.cellSize * 1.4)
const strokeWidth = computed(() => props.cellSize * 0.08)
const radius = computed(() => (ringSize.value - strokeWidth.value) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

// Progress as percentage
const progressPercent = computed(() => props.progress * 100)

// Dash offset for arc (starts at top, goes clockwise)
const dashOffset = computed(() => {
  return circumference.value * (1 - props.progress)
})

// Glow intensity increases with progress
const glowIntensity = computed(() => {
  return 4 + props.progress * 8
})

// One generic ring colour for every affordance: presentation is never inferred from an
// affordance's name (PDR-0025).
const progressColor = 'var(--color-warning)'
</script>

<style scoped>
.progress-ring {
  animation: fade-in 0.3s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Progress arc animation */
.progress-arc {
  transform-origin: center;
  transform: rotate(-90deg); /* Start from top */
  transition: stroke-dashoffset 0.3s ease-out;
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% {
    opacity: 0.9;
  }
  50% {
    opacity: 1;
  }
}

/* Center pulse effect */
.center-pulse {
  animation: pulse-center 2s ease-in-out infinite;
}

@keyframes pulse-center {
  0%, 100% {
    opacity: 0.1;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(1.2);
  }
}

/* Progress text */
.progress-text {
  animation: fade-pulse 2s ease-in-out infinite;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
}

@keyframes fade-pulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}
</style>
