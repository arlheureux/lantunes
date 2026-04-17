<template>
  <div class="album-card" @click="$emit('click')" @contextmenu.prevent="$emit('contextmenu', $event)">
    <div class="album-cover">
      <img v-if="artwork" :src="artworkUrl" :alt="title" />
      <div v-else class="album-placeholder">
        <i class="fas fa-compact-disc"></i>
      </div>
      <div class="album-play-btn" @click.stop="$emit('play')">
        <i class="fas fa-play"></i>
      </div>
    </div>
    <div class="name">{{ title }}</div>
    <div class="artist">{{ artist }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getMediaUrl } from '../../api/index.js'

const props = defineProps({
  id: {
    type: [Number, String],
    required: true
  },
  title: {
    type: String,
    required: true
  },
  artist: {
    type: String,
    default: ''
  },
  artwork: {
    type: String,
    default: null
  },
  artworkType: {
    type: String,
    default: 'album'
  }
})

defineEmits(['click', 'play', 'contextmenu'])

const artworkUrl = computed(() => {
  const path = props.artworkType === 'artist'
    ? `/api/library/artwork/artist/${props.id}`
    : `/api/library/artwork/${props.id}`
  return getMediaUrl(path)
})
</script>

<style scoped>
.album-card {
  cursor: pointer;
  transition: transform var(--transition-normal);
}

.album-card:hover {
  transform: translateY(-6px);
}

.album-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  margin-bottom: 14px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
}

.album-card:hover .album-cover img {
  box-shadow: var(--shadow-lg);
  transform: scale(1.02);
}

.album-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-surface) 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: placeholder-pulse 3s ease-in-out infinite;
}

@keyframes placeholder-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.album-placeholder i {
  font-size: 48px;
  color: #555;
}

.album-play-btn {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  opacity: 0;
  transform: translateY(12px);
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-lg);
}

.album-card:hover .album-play-btn {
  opacity: 1;
  transform: translateY(0);
}

.album-play-btn:hover {
  transform: scale(1.08) !important;
  background: var(--accent-hover);
}

.name {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

.artist {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
