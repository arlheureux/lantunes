<template>
  <div class="artist-detail">
    <button class="back-btn" @click="$emit('back')">
      <i class="fas fa-arrow-left"></i>
      Back
    </button>

    <div class="artist-header">
      <img
        v-if="artist?.image_url"
        :src="artist.image_url"
        :alt="artist.name"
        class="artist-image"
      />
      <div v-else class="artist-image placeholder">
        <span>{{ artist?.name?.charAt(0)?.toUpperCase() || '?' }}</span>
      </div>
      <div class="artist-info">
        <h1 class="artist-name">{{ artist?.name || 'Unknown Artist' }}</h1>
        <p class="artist-meta">
          {{ artist?.album_count || 0 }} albums
          <span v-if="artist?.track_count"> • {{ artist.track_count }} tracks</span>
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <div v-else-if="albums.length" class="artist-albums">
      <h2>Albums</h2>
      <AlbumGrid
        :albums="albums"
        :loading="false"
        @select-album="selectAlbum"
      />
    </div>

    <div v-if="topTracks.length" class="artist-tracks">
      <h2>Top Tracks</h2>
      <TrackList
        :tracks="topTracks"
        :show-album="false"
        @play="$emit('play', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import AlbumGrid from './AlbumGrid.vue'
import TrackList from './TrackList.vue'
import { api } from '@/api'

const props = defineProps({
  artist: Object
})

const emit = defineEmits(['back', 'play'])

const albums = ref([])
const topTracks = ref([])
const loading = ref(false)

const selectAlbum = (album) => {
  // Navigate to album detail
}

const loadArtistData = async () => {
  if (!props.artist?.id) return
  loading.value = true
  try {
    const response = await api.get(`/api/artists/${props.artist.id}`)
    albums.value = response.albums || []
    topTracks.value = response.top_tracks || []
  } catch (err) {
    console.error('Failed to load artist data:', err)
  } finally {
    loading.value = false
  }
}

watch(() => props.artist?.id, loadArtistData)
onMounted(loadArtistData)
</script>

<style scoped>
.artist-detail {
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

.artist-header {
  display: flex;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.artist-image {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: var(--shadow-lg);
}

.artist-image.placeholder {
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.artist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.artist-name {
  font-size: 2rem;
  margin: 0 0 0.5rem;
}

.artist-meta {
  color: var(--text-secondary);
  margin: 0;
}

.artist-albums,
.artist-tracks {
  margin-bottom: var(--space-xl);
}

.artist-albums h2,
.artist-tracks h2 {
  font-size: 1.25rem;
  margin: 0 0 var(--space-md);
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--space-xl);
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--bg-tertiary);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .artist-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .artist-image {
    width: 150px;
    height: 150px;
  }

  .artist-name {
    font-size: 1.5rem;
  }
}
</style>
