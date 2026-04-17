import { ref, computed } from 'vue'
import * as api from '../api/index.js'

export function useLibrary() {
  const albums = ref([])
  const recentAlbums = ref([])
  const artists = ref([])
  const playlists = ref([])
  const genres = ref([])
  const config = ref({ library: { music_path: '' } })
  const loading = ref({
    library: false,
    tracks: false
  })

  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'.split('')
  const selectedLetter = ref('A')
  const selectedAlbumLetter = ref('A')
  const selectedGenreLetter = ref(null)

  const filteredArtists = computed(() => {
    if (!selectedLetter.value) return artists.value
    return artists.value.filter(a => {
      const firstChar = a.name.charAt(0).toUpperCase()
      if (selectedLetter.value === '#') return !'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.includes(firstChar)
      return firstChar === selectedLetter.value
    })
  })

  const filteredAlbums = computed(() => {
    if (!selectedAlbumLetter.value) return albums.value
    return albums.value.filter(a => {
      const firstChar = a.title.charAt(0).toUpperCase()
      if (selectedAlbumLetter.value === '#') return !'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.includes(firstChar)
      return firstChar === selectedAlbumLetter.value
    })
  })

  const filteredGenres = computed(() => {
    if (!selectedGenreLetter.value) return genres.value
    return genres.value.filter(g => {
      const firstChar = g.charAt(0).toUpperCase()
      if (selectedGenreLetter.value === '#') return !'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.includes(firstChar)
      return firstChar === selectedGenreLetter.value
    })
  })

  async function loadLibrary() {
    loading.value.library = true
    try {
      const [a, ra, ar, p, g, c] = await Promise.all([
        api.getAlbums(),
        api.getRecentAlbums(),
        api.getArtists(),
        api.getPlaylists(),
        api.getGenres(),
        api.getConfig()
      ])
      if (a) albums.value = a
      if (ra) recentAlbums.value = ra
      if (ar) artists.value = ar
      if (p) playlists.value = p
      if (g) genres.value = g
      if (c) config.value = c
    } finally {
      loading.value.library = false
    }
  }

  async function loadArtist(id) {
    return api.getArtist(id)
  }

  async function loadAlbum(id) {
    return api.getAlbum(id)
  }

  async function loadPlaylist(id) {
    return api.getPlaylist(id)
  }

  async function loadGenreAlbums(genre) {
    return api.getGenreAlbums(genre)
  }

  async function loadFavorites() {
    return api.getFavorites()
  }

  async function search(query) {
    return api.search(query)
  }

  return {
    albums,
    recentAlbums,
    artists,
    playlists,
    genres,
    config,
    loading,
    letters,
    selectedLetter,
    selectedAlbumLetter,
    selectedGenreLetter,
    filteredArtists,
    filteredAlbums,
    filteredGenres,
    loadLibrary,
    loadArtist,
    loadAlbum,
    loadPlaylist,
    loadGenreAlbums,
    loadFavorites,
    search
  }
}
