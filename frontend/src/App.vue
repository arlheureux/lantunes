<template>
  <div class="app-container" :data-theme="theme">
    <Sidebar
      :current-view="currentView"
      :is-admin="isAdmin"
      @navigate="handleNavigate"
      @settings="showSettings = true"
    />

    <main class="main-content">
      <div class="content-area">
        <header class="content-header">
          <h1 class="view-title">{{ viewTitle }}</h1>
          <div class="header-actions">
            <button v-if="isAdmin" class="action-btn" @click="triggerScan">
              <i class="fas fa-sync"></i>
              Scan Library
            </button>
          </div>
        </header>

        <div class="content-scroll">
          <AlbumGrid
            v-if="currentView === 'albums'"
            :albums="albums"
            :loading="loadingAlbums"
            @select-album="selectAlbum"
          />

          <ArtistList
            v-else-if="currentView === 'artists'"
            :artists="artists"
            :loading="loadingArtists"
            @select="selectArtist"
          />

          <GenreList
            v-else-if="currentView === 'genres'"
            :genres="genres"
            :loading="loadingGenres"
            @select="selectGenre"
          />

          <TrackList
            v-else-if="currentView === 'tracks'"
            :tracks="[]"
            :loading="loadingTracks"
            @play="playTrack"
          />

          <div v-else-if="currentView === 'favorites'" class="view-container">
            <h2>Favorites</h2>
            <TrackList
              :tracks="favorites"
              :loading="loadingFavorites"
              @play="playTrack"
            />
          </div>

          <div v-else-if="currentView === 'playlists'" class="view-container">
            <div class="playlist-header">
              <h2>Playlists</h2>
              <button class="btn btn-primary" @click="createPlaylist">
                <i class="fas fa-plus"></i>
                New Playlist
              </button>
            </div>
            <div v-if="loadingPlaylists" class="loading">
              <div class="spinner"></div>
            </div>
            <div v-else class="playlist-grid">
              <div
                v-for="playlist in playlists"
                :key="playlist.id"
                class="playlist-card"
                @click="selectPlaylist(playlist)"
              >
                <div class="playlist-icon">
                  <i class="fas fa-list"></i>
                </div>
                <div class="playlist-info">
                  <h3>{{ playlist.name }}</h3>
                  <p>{{ playlist.track_count || 0 }} tracks</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="currentView === 'queue'" class="view-container">
            <h2>Queue</h2>
            <TrackList
              :tracks="queue"
              @play="playTrack"
            />
          </div>

          <div v-else-if="currentView === 'search'" class="view-container">
            <div class="search-bar">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search music..."
                class="search-input"
                @input="debouncedSearch"
              />
            </div>
            <div v-if="searchResults.length" class="search-results">
              <TrackList :tracks="searchResults" @play="playTrack" />
            </div>
            <div v-else-if="searchQuery && !searching" class="empty-state">
              No results found
            </div>
          </div>

          <div v-else-if="currentView === 'album-detail'" class="view-container">
            <AlbumDetail
              :album="selectedAlbum"
              @play="playTrack"
              @back="currentView = 'albums'"
            />
          </div>

          <div v-else-if="currentView === 'playlist-detail'" class="view-container">
            <PlaylistDetail
              :playlist="selectedPlaylist"
              @play="playTrack"
              @back="currentView = 'playlists'"
            />
          </div>

          <div v-else-if="currentView === 'artist-detail'" class="view-container">
            <ArtistDetail
              :artist="selectedArtist"
              @play="playTrack"
              @back="currentView = 'artists'"
            />
          </div>
        </div>
      </div>
    </main>

    <MobileNav
      v-if="isMobile"
      :current-view="currentView"
      @navigate="handleNavigate"
    />

    <PlayerBar
      v-if="hasCurrentTrack"
      @expand="showPlayerModal = true"
      @show-queue="currentView = 'queue'"
    />

    <PlayerModal v-model="showPlayerModal" @show-queue="currentView = 'queue'" />

    <SettingsModal v-model="showSettings" />

    <Toast />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import MobileNav from '@/components/layout/MobileNav.vue'
import AlbumGrid from '@/components/library/AlbumGrid.vue'
import TrackList from '@/components/library/TrackList.vue'
import ArtistList from '@/components/library/ArtistList.vue'
import GenreList from '@/components/library/GenreList.vue'
import PlayerBar from '@/components/player/PlayerBar.vue'
import PlayerModal from '@/components/player/PlayerModal.vue'
import SettingsModal from '@/components/settings/SettingsModal.vue'
import Toast from '@/components/common/Toast.vue'
import { useAuth } from '@/composables/useAuth'
import { useLibrary } from '@/composables/useLibrary'
import { usePlayer } from '@/composables/usePlayer'
import { useToast } from '@/composables/useToast'

const { user, isAdmin } = useAuth()
const {
  albums, artists, genres, playlists, favorites, queue,
  loadingAlbums, loadingArtists, loadingGenres, loadingPlaylists, loadingFavorites, loadingTracks,
  searchResults, searching,
  loadAlbums, loadArtists, loadGenres, loadPlaylists, loadFavorites, loadQueue,
  searchMusic, triggerScan, createPlaylist, selectAlbum, selectArtist, selectGenre, selectPlaylist, selectedAlbum, selectedArtist, selectedPlaylist
} = useLibrary()

const { playTrack, hasCurrentTrack } = usePlayer()
const { showToast } = useToast()

const theme = ref('dark')
const currentView = ref('albums')
const showSettings = ref(false)
const showPlayerModal = ref(false)
const searchQuery = ref('')
const isMobile = ref(false)

const viewTitle = computed(() => {
  const titles = {
    albums: 'Albums',
    artists: 'Artists',
    genres: 'Genres',
    favorites: 'Favorites',
    playlists: 'Playlists',
    queue: 'Queue',
    search: 'Search',
    'album-detail': selectedAlbum.value?.title || 'Album',
    'artist-detail': selectedArtist.value?.name || 'Artist',
    'playlist-detail': selectedPlaylist.value?.name || 'Playlist'
  }
  return titles[currentView.value] || 'Library'
})

const handleNavigate = (view) => {
  currentView.value = view
}

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    if (searchQuery.value.length >= 2) {
      searchMusic(searchQuery.value)
    }
  }, 300)
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const initData = async () => {
  try {
    await Promise.all([
      loadAlbums(),
      loadArtists(),
      loadGenres(),
      loadPlaylists(),
      loadFavorites()
    ])
  } catch (err) {
    showToast('Failed to load library', 'error')
  }
}

watch(currentView, (view) => {
  if (view === 'queue') {
    loadQueue()
  }
})

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  initData()
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-subtle);
}

.view-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.action-btn {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  transition: all var(--transition);
}

.action-btn:hover {
  background: var(--bg-tertiary);
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.view-container {
  padding: var(--space-md);
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.playlist-header h2 {
  margin: 0;
}

.playlist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-md);
}

.playlist-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
}

.playlist-card:hover {
  background: var(--bg-tertiary);
}

.playlist-icon {
  width: 48px;
  height: 48px;
  background: var(--primary);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.playlist-info h3 {
  margin: 0 0 0.25rem;
  font-size: 0.95rem;
}

.playlist-info p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.search-bar {
  margin-bottom: var(--space-lg);
}

.search-input {
  width: 100%;
  padding: var(--space-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary);
}

.empty-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-secondary);
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

.btn {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  transition: all var(--transition);
}

.btn-primary {
  background: var(--primary);
  border: none;
  color: white;
}

.btn-primary:hover {
  background: var(--primary-hover);
}

@media (max-width: 768px) {
  .content-header {
    padding: var(--space-sm) var(--space-md);
  }

  .view-title {
    font-size: 1.25rem;
  }

  .content-scroll {
    padding-bottom: 80px;
  }
}
</style>
