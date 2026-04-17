import { ref, computed } from 'vue'
import * as api from '../api/index.js'

export function useLibrary() {
  const albums = ref([])
  const recentAlbums = ref([])
  const artists = ref([])
  const playlists = ref([])
  const favorites = ref([])
  const genres = ref([])
  const queue = ref([])
  const searchResults = ref([])
  const config = ref({ library: { music_path: '' } })

  const loadingAlbums = ref(false)
  const loadingArtists = ref(false)
  const loadingGenres = ref(false)
  const loadingPlaylists = ref(false)
  const loadingFavorites = ref(false)
  const loadingTracks = ref(false)
  const searching = ref(false)

  const selectedAlbum = ref(null)
  const selectedArtist = ref(null)
  const selectedPlaylist = ref(null)

  async function loadAlbums() {
    loadingAlbums.value = true
    try {
      const data = await api.getAlbums()
      if (data) albums.value = data
    } finally {
      loadingAlbums.value = false
    }
  }

  async function loadArtists() {
    loadingArtists.value = true
    try {
      const data = await api.getArtists()
      if (data) artists.value = data
    } finally {
      loadingArtists.value = false
    }
  }

  async function loadGenres() {
    loadingGenres.value = true
    try {
      const data = await api.getGenres()
      if (data) genres.value = data
    } finally {
      loadingGenres.value = false
    }
  }

  async function loadPlaylists() {
    loadingPlaylists.value = true
    try {
      const data = await api.getPlaylists()
      if (data) playlists.value = data
    } finally {
      loadingPlaylists.value = false
    }
  }

  async function loadFavorites() {
    loadingFavorites.value = true
    try {
      const data = await api.getFavorites()
      if (data) favorites.value = data
    } finally {
      loadingFavorites.value = false
    }
  }

  async function loadQueue() {
    // Queue is managed by usePlayer, this is for display
  }

  async function searchMusic(query) {
    searching.value = true
    try {
      const data = await api.search(query)
      if (data) searchResults.value = data
    } finally {
      searching.value = false
    }
  }

  async function triggerScan() {
    // Admin function to trigger library scan
    return api.apiCall('/api/library/scan', { method: 'POST' })
  }

  async function createPlaylist(name) {
    return api.createPlaylist(name)
  }

  function selectAlbum(album) {
    selectedAlbum.value = album
  }

  function selectArtist(artist) {
    selectedArtist.value = artist
  }

  function selectPlaylist(playlist) {
    selectedPlaylist.value = playlist
  }

  function selectGenre(genre) {
    // Navigate to genre view
  }

  return {
    albums,
    recentAlbums,
    artists,
    playlists,
    favorites,
    genres,
    queue,
    searchResults,
    config,
    loadingAlbums,
    loadingArtists,
    loadingGenres,
    loadingPlaylists,
    loadingFavorites,
    loadingTracks,
    searching,
    selectedAlbum,
    selectedArtist,
    selectedPlaylist,
    loadAlbums,
    loadArtists,
    loadGenres,
    loadPlaylists,
    loadFavorites,
    loadQueue,
    searchMusic,
    triggerScan,
    createPlaylist,
    selectAlbum,
    selectArtist,
    selectPlaylist,
    selectGenre
  }
}
