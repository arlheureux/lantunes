<template>
  <div class="track-list">
    <div
      v-for="track in tracks"
      :key="track.id"
      class="track-row"
      :class="{ playing: isPlaying(track.id) }"
      @click="$emit('play', track)"
      @contextmenu.prevent="$emit('contextmenu', $event, track)"
    >
      <span class="title">
        <i v-if="isPlaying(track.id)" class="fas fa-volume-up playing-icon"></i>
        {{ track.title }}
      </span>
      <span class="duration">{{ formatDuration(track.duration) }}</span>
      <button class="menu-btn" @click.stop="$emit('contextmenu', $event, track)">
        <i class="fas fa-ellipsis-h"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tracks: {
    type: Array,
    required: true
  },
  currentTrackId: {
    type: Number,
    default: null
  }
})

defineEmits(['play', 'contextmenu'])

function isPlaying(trackId) {
  return trackId === currentTrackId
}

function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return mins + ':' + secs.toString().padStart(2, '0')
}
</script>

<style scoped>
.track-list {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.track-row {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.track-row:last-child {
  border-bottom: none;
}

.track-row:hover {
  background: var(--bg-hover);
}

.track-row.playing {
  background: var(--accent-muted);
}

.track-row.playing .title {
  color: var(--accent);
}

.title {
  flex: 1;
  font-size: 15px;
  padding-right: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration {
  color: var(--text-muted);
  font-size: 13px;
  min-width: 48px;
  text-align: right;
}

.menu-btn {
  opacity: 0;
  margin-left: 12px;
  color: var(--text-secondary);
  transition: opacity var(--transition-fast);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}

.track-row:hover .menu-btn {
  opacity: 1;
}

.menu-btn:hover {
  color: var(--text-primary);
}

.playing-icon {
  color: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
