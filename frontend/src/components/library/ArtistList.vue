<template>
  <div class="artist-list">
    <div class="artist-grid">
      <div
        v-for="artist in artists"
        :key="artist.id"
        class="artist-card"
        @click="$emit('select', artist)"
      >
        <div class="artist-image">
          <img
            v-if="artist.image_url"
            :src="artist.image_url"
            :alt="artist.name"
          />
          <div v-else class="artist-placeholder">
            <span>{{ artist.name.charAt(0).toUpperCase() }}</span>
          </div>
        </div>
        <div class="artist-info">
          <h3 class="artist-name">{{ artist.name }}</h3>
          <p class="artist-meta">{{ artist.album_count || 0 }} albums</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading artists...</span>
    </div>

    <div v-else-if="!artists.length" class="empty-state">
      <span class="empty-icon">🎵</span>
      <p>No artists found</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  artists: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['select'])
</script>

<style scoped>
.artist-list {
  padding: var(--space-md);
}

.artist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-lg);
}

.artist-card {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
}

.artist-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.artist-image {
  aspect-ratio: 1;
  overflow: hidden;
}

.artist-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition);
}

.artist-card:hover .artist-image img {
  transform: scale(1.05);
}

.artist-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.artist-info {
  padding: var(--space-sm) var(--space-md);
}

.artist-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist-meta {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  color: var(--text-secondary);
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--bg-tertiary);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: var(--space-sm);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--space-sm);
}
</style>
