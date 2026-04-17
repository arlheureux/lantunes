<template>
  <div class="genre-list">
    <div class="genre-grid">
      <div
        v-for="genre in genres"
        :key="genre.name"
        class="genre-card"
        :style="{ '--genre-color': getGenreColor(genre.name) }"
        @click="$emit('select', genre)"
      >
        <div class="genre-pattern"></div>
        <div class="genre-content">
          <h3 class="genre-name">{{ genre.name }}</h3>
          <p class="genre-count">{{ genre.track_count || 0 }} tracks</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading genres...</span>
    </div>

    <div v-else-if="!genres.length" class="empty-state">
      <span class="empty-icon">🏷️</span>
      <p>No genres found</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  genres: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['select'])

const getGenreColor = (name) => {
  const colors = [
    '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
    '#f97316', '#eab308', '#22c55e', '#14b8a6',
    '#06b6d4', '#3b82f6'
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}
</script>

<style scoped>
.genre-list {
  padding: var(--space-md);
}

.genre-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-md);
}

.genre-card {
  position: relative;
  height: 100px;
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
}

.genre-card:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-lg);
}

.genre-pattern {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--genre-color), color-mix(in srgb, var(--genre-color) 70%, black));
  opacity: 0.9;
}

.genre-pattern::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      45deg,
      transparent,
      transparent 10px,
      rgba(255,255,255,0.03) 10px,
      rgba(255,255,255,0.03) 20px
    );
}

.genre-content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: var(--space-md);
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
}

.genre-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.genre-count {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.8);
  margin: 0.25rem 0 0;
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
