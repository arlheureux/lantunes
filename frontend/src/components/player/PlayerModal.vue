<template>
  <Modal :model-value="modelValue" size="fullscreen" :show-close="true" @close="close" @update:model-value="$emit('update:modelValue', $event)">
    <div class="player-modal">
      <div class="player-visualization" :style="visualizationStyle">
        <div class="visualizer-bars">
          <div v-for="i in 32" :key="i" class="viz-bar" :style="{ '--delay': `${i * 0.05}s` }"></div>
        </div>
      </div>

      <div class="player-content">
        <div class="album-art-container">
          <img
            v-if="currentTrack?.cover_url"
            :src="currentTrack.cover_url"
            :alt="currentTrack?.title"
            class="album-art-large"
          />
          <div v-else class="album-art-placeholder">
            <span>{{ currentTrack?.title?.charAt(0)?.toUpperCase() || '?' }}</span>
          </div>
        </div>

        <div class="track-info">
          <h1 class="track-title">{{ currentTrack?.title || 'No track playing' }}</h1>
          <p class="track-artist">{{ currentTrack?.artist_name || 'Unknown artist' }}</p>
          <p class="track-album">{{ currentTrack?.album_name || 'Unknown album' }}</p>
        </div>

        <div class="progress-section">
          <span class="time-current">{{ formatTime(currentTime) }}</span>
          <div class="progress-bar-container" @click="seek">
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>
          <span class="time-total">{{ formatTime(duration) }}</span>
        </div>

        <div class="controls-section">
          <button class="control-btn shuffle" :class="{ active: shuffle }" @click="toggleShuffle">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/></svg>
          </button>
          <button class="control-btn prev" @click="previous">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
          </button>
          <button class="control-btn play-pause" @click="togglePlay">
            <svg v-if="!isPlaying" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          </button>
          <button class="control-btn next" @click="next">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
          </button>
          <button class="control-btn repeat" :class="{ active: repeat !== 'none' }" @click="cycleRepeat">
            <svg v-if="repeat === 'all'" viewBox="0 0 24 24" fill="currentColor"><path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/></svg>
            <svg v-else-if="repeat === 'one'" viewBox="0 0 24 24" fill="currentColor"><path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z" transform="scale(-1,1) translate(-24,0)"/></svg>
          </button>
        </div>

        <div class="secondary-controls">
          <button class="control-btn volume-btn" @click="toggleMute">
            <svg v-if="volume === 0 || muted" viewBox="0 0 24 24" fill="currentColor"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
            <svg v-else-if="volume < 0.5" viewBox="0 0 24 24" fill="currentColor"><path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
          </button>
          <input
            type="range"
            class="volume-slider"
            min="0"
            max="1"
            step="0.01"
            :value="muted ? 0 : volume"
            @input="setVolume($event.target.value)"
          />
          <button class="control-btn queue-btn" @click="$emit('showQueue')">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/></svg>
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup>
import { computed } from 'vue'
import Modal from '@/components/common/Modal.vue'
import { usePlayer } from '@/composables/usePlayer'

defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'showQueue'])

const {
  currentTrack,
  isPlaying,
  currentTime,
  duration,
  volume,
  muted,
  shuffle,
  repeat,
  play,
  pause,
  previous,
  next,
  seek,
  setVolume,
  toggleMute,
  setShuffle,
  setRepeat
} = usePlayer()

const progressPercent = computed(() => {
  if (!duration) return 0
  return (currentTime.value / duration.value) * 100
})

const visualizationStyle = computed(() => ({
  '--viz-color': currentTrack.value?.cover_url
    ? 'var(--primary)'
    : 'var(--text-secondary)'
}))

const togglePlay = () => {
  if (isPlaying.value) pause()
  else play()
}

const toggleShuffle = () => setShuffle(!shuffle.value)

const cycleRepeat = () => {
  const modes = ['none', 'all', 'one']
  const currentIndex = modes.indexOf(repeat.value)
  setRepeat(modes[(currentIndex + 1) % modes.length])
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const close = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.player-modal {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.player-visualization {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
  overflow: hidden;
}

.visualizer-bars {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  height: 150px;
  align-items: flex-end;
}

.viz-bar {
  width: 6px;
  background: var(--viz-color);
  border-radius: 3px 3px 0 0;
  opacity: 0.3;
  animation: viz-pulse 0.5s ease-in-out infinite alternate;
  animation-delay: var(--delay);
}

@keyframes viz-pulse {
  from { height: 20px; }
  to { height: 80px; }
}

.player-content {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  gap: var(--space-lg);
}

.album-art-container {
  width: min(350px, 60vw);
  aspect-ratio: 1;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.album-art-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-art-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.track-info {
  text-align: center;
}

.track-title {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: var(--text-primary);
}

.track-artist {
  font-size: 1.1rem;
  color: var(--primary);
  margin: 0 0 0.25rem;
}

.track-album {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
}

.progress-section {
  width: 100%;
  max-width: 500px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.time-current,
.time-total {
  font-size: 0.8rem;
  color: var(--text-secondary);
  min-width: 40px;
  font-variant-numeric: tabular-nums;
}

.time-total {
  text-align: right;
}

.progress-bar-container {
  flex: 1;
  height: 24px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.progress-bar-bg {
  width: 100%;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  transition: height var(--transition);
}

.progress-bar-container:hover .progress-bar-bg {
  height: 6px;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.controls-section {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.control-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: var(--space-sm);
  border-radius: 50%;
  transition: all var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn svg {
  width: 24px;
  height: 24px;
}

.control-btn:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.control-btn.active {
  color: var(--primary);
}

.control-btn.shuffle svg,
.control-btn.repeat svg {
  width: 20px;
  height: 20px;
}

.control-btn.prev svg,
.control-btn.next svg {
  width: 28px;
  height: 28px;
}

.control-btn.play-pause {
  width: 64px;
  height: 64px;
  background: var(--primary);
  color: white;
}

.control-btn.play-pause svg {
  width: 32px;
  height: 32px;
}

.control-btn.play-pause:hover {
  background: var(--primary-hover);
  transform: scale(1.05);
}

.secondary-controls {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.volume-slider {
  width: 100px;
  height: 4px;
  appearance: none;
  background: var(--bg-tertiary);
  border-radius: 2px;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
}
</style>
