<template>
  <div v-if="track" class="player-bar-desktop">
    <div class="track-info">
      <div class="track-artwork" @click="$emit('showModal')">
        <img v-if="track.album_id" :src="artworkUrl" @error="$event.target.style.display='none'" />
      </div>
      <div>
        <div class="title">{{ track.title }}</div>
        <div class="artist">{{ track.artist }}</div>
      </div>
    </div>

    <div class="player-controls">
      <div class="control-buttons">
        <button @click="$emit('previous')" title="Previous">
          <i class="fas fa-step-backward"></i>
        </button>
        <button class="play-btn" :class="{ loading: isLoading }" @click="$emit('togglePlay')" title="Play/Pause">
          <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
          <i v-else :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
        </button>
        <button @click="$emit('next')" title="Next">
          <i class="fas fa-step-forward"></i>
        </button>
        <button @click="$emit('toggleShuffle')" :style="{ color: shuffleMode ? 'var(--accent)' : 'var(--text-secondary)' }" title="Shuffle">
          <i class="fas fa-random"></i>
        </button>
        <button @click="$emit('toggleRepeat')" :style="{ color: repeatMode !== 'off' ? 'var(--accent)' : 'var(--text-secondary)' }" title="Repeat">
          <i class="fas fa-redo"></i>
          <span v-if="repeatMode === 'one'" style="font-size:10px;position:absolute;margin-left:-8px;margin-top:8px;">1</span>
        </button>
      </div>
      <div class="progress">
        <span>{{ formatDuration(position) }}</span>
        <div class="progress-bar" @click="$emit('seek', $event)">
          <div class="fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span>{{ formatDuration(track.duration) }}</span>
      </div>
      <div class="track-meta">
        <span v-if="track.file_format">{{ track.file_format }}</span>
        <span v-if="track.bitrate"> · {{ track.bitrate }}kbps</span>
        <span v-if="track.sample_rate"> · {{ track.sample_rate }}Hz</span>
      </div>
    </div>

    <div class="device-selector" v-if="sessions.length > 1">
      <select v-model="selectedSession" @change="$emit('setPlayer', selectedSession)" title="Select playback session">
        <option v-for="s in sessions" :key="s.id" :value="s.id">
          {{ s.is_player ? '🎵 ' : '📱 ' }}{{ s.device_name }}
        </option>
      </select>
    </div>

    <div class="volume">
      <i class="fas fa-volume-up"></i>
      <input type="range" min="0" max="1" step="0.01" :value="volume" @input="$emit('setVolume', parseFloat($event.target.value))" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getMediaUrl } from '../../api/index.js'

const props = defineProps({
  track: Object,
  position: { type: Number, default: 0 },
  isPlaying: Boolean,
  isLoading: Boolean,
  volume: { type: Number, default: 1.0 },
  shuffleMode: Boolean,
  repeatMode: { type: String, default: 'off' },
  progressPercent: { type: Number, default: 0 },
  sessions: { type: Array, default: () => [] }
})

const emit = defineEmits([
  'togglePlay', 'previous', 'next', 'seek', 'setVolume',
  'toggleShuffle', 'toggleRepeat', 'showModal', 'setPlayer'
])

const artworkUrl = computed(() => {
  if (!props.track?.album_id) return ''
  return getMediaUrl(`/api/library/artwork/${props.track.album_id}`)
})

const selectedSession = computed({
  get() {
    const player = props.sessions.find(s => s.is_player)
    return player?.id
  },
  set() {}
})

function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return mins + ':' + secs.toString().padStart(2, '0')
}
</script>

<style scoped>
.player-bar-desktop {
  height: var(--player-height);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  flex-shrink: 0;
}

.track-info {
  width: var(--sidebar-width);
  display: flex;
  align-items: center;
  gap: 14px;
}

.track-artwork {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.track-artwork img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-info .title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-info .artist {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  max-width: 600px;
  margin: 0 auto;
}

.control-buttons {
  display: flex;
  align-items: center;
  gap: 28px;
}

.control-buttons button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 18px;
  transition: all var(--transition-fast);
  padding: 8px;
  position: relative;
}

.control-buttons button:hover {
  color: var(--text-primary);
  transform: scale(1.1);
}

.control-buttons .play-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--text-primary);
  color: var(--bg-base);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.control-buttons .play-btn:hover {
  transform: scale(1.05);
}

.control-buttons .play-btn.loading {
  opacity: 0.7;
  cursor: wait;
}

.progress {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress span {
  font-size: 11px;
  color: var(--text-muted);
  min-width: 38px;
  font-variant-numeric: tabular-nums;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--bg-elevated);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  transition: height var(--transition-fast);
}

.progress-bar:hover {
  height: 6px;
}

.progress-bar .fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  position: relative;
}

.progress-bar:hover .fill::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  background: var(--text-primary);
  border-radius: 50%;
  box-shadow: var(--shadow-sm);
}

.track-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 6px;
}

.device-selector {
  margin-left: 16px;
}

.device-selector select {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  padding: 10px 14px;
  border-radius: var(--radius-full);
  font-size: 13px;
  cursor: pointer;
  outline: none;
  min-width: 130px;
  font-family: inherit;
}

.device-selector select:hover {
  background: var(--bg-hover);
}

.volume {
  width: 140px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.volume i {
  color: var(--text-secondary);
  font-size: 14px;
}

.volume input {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: var(--bg-elevated);
  border-radius: 2px;
  cursor: pointer;
}

.volume input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
}

@media (max-width: 1024px) {
  .player-bar-desktop {
    display: none;
  }
}
</style>
