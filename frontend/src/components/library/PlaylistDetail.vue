<template>
  <div class="playlist-detail">
    <button class="back-btn" @click="$emit('back')">
      <i class="fas fa-arrow-left"></i>
      Back
    </button>

    <div class="playlist-header">
      <div class="playlist-icon">
        <i class="fas fa-list"></i>
      </div>
      <div class="playlist-info">
        <h1 class="playlist-name">{{ playlist?.name || 'Unknown Playlist' }}</h1>
        <p class="playlist-meta">
          {{ playlist?.track_count || 0 }} tracks
          <span v-if="playlist?.duration"> • {{ formatDuration(playlist.duration) }}</span>
        </p>
        <div class="playlist-actions">
          <button class="btn btn-primary" @click="playAll">
            <i class="fas fa-play"></i>
            Play
          </button>
          <button class="btn btn-secondary" @click="shuffleAll">
            <i class="fas fa-random"></i>
            Shuffle
          </button>
          <button class="btn btn-icon" @click="showAddTracks = true">
            <i class="fas fa-plus"></i>
          </button>
          <button class="btn btn-icon danger" @click="deletePlaylist">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <TrackList
      :tracks="tracks"
      :loading="loading"
      :show-album="true"
      @play="$emit('play', $event)"
    />

    <Modal v-model="showAddTracks" title="Add Tracks">
      <div class="add-tracks-modal">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search tracks..."
          class="search-input"
        />
        <div class="search-results">
          <div
            v-for="track in searchResults"
            :key="track.id"
            class="search-result-item"
            @click="addTrack(track)"
          >
            <span class="track-title">{{ track.title }}</span>
            <span class="track-artist">{{ track.artist_name }}</span>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import TrackList from './TrackList.vue'
import Modal from '@/components/common/Modal.vue'
import { api } from '@/api'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  playlist: Object
})

const emit = defineEmits(['back', 'play'])

const { showToast } = useToast()

const tracks = ref([])
const loading = ref(false)
const showAddTracks = ref(false)
const searchQuery = ref('')
const searchResults = ref([])

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins}m`
}

const playAll = () => {
  if (tracks.value.length) {
    emit('play', { tracks: tracks.value, index: 0 })
  }
}

const shuffleAll = () => {
  if (tracks.value.length) {
    const shuffled = [...tracks.value].sort(() => Math.random() - 0.5)
    emit('play', { tracks: shuffled, index: 0 })
  }
}

const loadPlaylistTracks = async () => {
  if (!props.playlist?.id) return
  loading.value = true
  try {
    const response = await api.get(`/api/playlists/${props.playlist.id}`)
    tracks.value = response.tracks || []
  } catch (err) {
    showToast('Failed to load playlist', 'error')
  } finally {
    loading.value = false
  }
}

const searchTracks = async () => {
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  try {
    searchResults.value = await api.get(`/api/search?q=${searchQuery.value}`)
  } catch (err) {
    console.error('Search failed:', err)
  }
}

const addTrack = async (track) => {
  try {
    await api.post(`/api/playlists/${props.playlist.id}/tracks`, {
      track_id: track.id
    })
    showToast('Track added', 'success')
    loadPlaylistTracks()
  } catch (err) {
    showToast('Failed to add track', 'error')
  }
}

const deletePlaylist = async () => {
  if (!confirm('Delete this playlist?')) return
  try {
    await api.delete(`/api/playlists/${props.playlist.id}`)
    showToast('Playlist deleted', 'success')
    emit('back')
  } catch (err) {
    showToast('Failed to delete playlist', 'error')
  }
}

watch(searchQuery, searchTracks)
watch(() => props.playlist?.id, loadPlaylistTracks)
onMounted(loadPlaylistTracks)
</script>

<style scoped>
.playlist-detail {
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

.playlist-header {
  display: flex;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.playlist-icon {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 4rem;
  box-shadow: var(--shadow-lg);
}

.playlist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.playlist-name {
  font-size: 2rem;
  margin: 0 0 0.5rem;
}

.playlist-meta {
  color: var(--text-secondary);
  margin: 0 0 var(--space-lg);
}

.playlist-actions {
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

.btn-icon {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
}

.btn-icon:hover {
  background: var(--bg-tertiary);
}

.btn-icon.danger:hover {
  background: var(--error);
  border-color: var(--error);
  color: white;
}

.add-tracks-modal {
  padding: var(--space-md);
}

.search-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  flex-direction: column;
  padding: var(--space-sm);
  border-radius: var(--radius);
  cursor: pointer;
}

.search-result-item:hover {
  background: var(--bg-tertiary);
}

.track-title {
  font-weight: 500;
}

.track-artist {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .playlist-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .playlist-icon {
    width: 150px;
    height: 150px;
    font-size: 3rem;
  }

  .playlist-name {
    font-size: 1.5rem;
  }
}
</style>
