<template>
  <div class="album-detail">
    <button class="back-btn" @click="$emit('back')">
      <i class="fas fa-arrow-left"></i>
      Back
    </button>

    <div class="album-header">
      <img
        v-if="album?.cover_url"
        :src="album.cover_url"
        :alt="album.title"
        class="album-cover"
      />
      <div v-else class="album-cover placeholder">
        <i class="fas fa-music"></i>
      </div>
      <div class="album-info">
        <h1 class="album-title">{{ album?.title || 'Unknown Album' }}</h1>
        <p class="album-artist">{{ album?.artist_name || 'Unknown Artist' }}</p>
        <p class="album-meta">
          {{ album?.year || '' }}
          <span v-if="album?.genre"> • {{ album.genre }}</span>
          <span v-if="album?.track_count"> • {{ album.track_count }} tracks</span>
        </p>
        <div class="album-actions">
          <button class="btn btn-primary" @click="playAll">
            <i class="fas fa-play"></i>
            Play All
          </button>
          <button class="btn btn-secondary" @click="shuffleAll">
            <i class="fas fa-random"></i>
            Shuffle
          </button>
        </div>
      </div>
    </div>

    <TrackList
      :tracks="album?.tracks || []"
      :show-album="false"
      @play="$emit('play', $event)"
    />
  </div>
</template>

<script setup>
import TrackList from './TrackList.vue'

defineProps({
  album: Object
})

const emit = defineEmits(['back', 'play'])

const playAll = () => {
  emit('play', { tracks: props.album?.tracks, index: 0 })
}

const props = defineProps({
  album: Object
})
</script>

<style scoped>
.album-detail {
  padding: var(--space-md);
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  font-size: 0.9rem;
}

.back-btn:hover {
  color: var(--text-primary);
}

.album-header {
  display: flex;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.album-cover {
  width: 200px;
  height: 200px;
  border-radius: var(--radius);
  object-fit: cover;
  box-shadow: var(--shadow-lg);
}

.album-cover.placeholder {
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 3rem;
}

.album-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.album-title {
  font-size: 2rem;
  margin: 0 0 0.5rem;
}

.album-artist {
  font-size: 1.1rem;
  color: var(--primary);
  margin: 0 0 0.5rem;
}

.album-meta {
  color: var(--text-secondary);
  margin: 0 0 var(--space-lg);
}

.album-actions {
  display: flex;
  gap: var(--space-sm);
}

.btn {
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.btn-primary {
  background: var(--primary);
  border: none;
  color: white;
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-secondary {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-tertiary);
}

@media (max-width: 768px) {
  .album-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .album-cover {
    width: 180px;
    height: 180px;
  }

  .album-title {
    font-size: 1.5rem;
  }
}
</style>
