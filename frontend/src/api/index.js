const API = ''

export function getAuthHeader() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function getMediaUrl(path) {
  const token = localStorage.getItem('access_token')
  const sep = path.includes('?') ? '&' : '?'
  return `${API}${path}${token ? sep + 'token=' + token : ''}`
}

export async function apiCall(url, opts = {}) {
  const token = localStorage.getItem('access_token')
  const headers = {
    ...opts.headers
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const res = await fetch(`${API}${url}`, { ...opts, headers })

    if (res.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login.html'
      return null
    }

    if (!res.ok) {
      console.error('API error:', res.status, await res.text())
      return null
    }

    return await res.json()
  } catch (e) {
    console.error('API exception:', e)
    return null
  }
}

export const api = {
  get: (url) => apiCall(url),
  post: (url, data) => apiCall(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  put: (url, data) => apiCall(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  delete: (url) => apiCall(url, { method: 'DELETE' })
}

// Auth API
export async function login(username, password) {
  return apiCall('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
}

// Library API
export async function getAlbums() {
  return apiCall('/api/library/albums')
}

export async function getRecentAlbums(limit = 8) {
  return apiCall(`/api/library/albums/recent?limit=${limit}`)
}

export async function getArtists() {
  return apiCall('/api/library/artists')
}

export async function getArtist(id) {
  return apiCall(`/api/library/artists/${id}`)
}

export async function getGenres() {
  return apiCall('/api/library/genres')
}

export async function getGenreAlbums(genre) {
  return apiCall(`/api/library/genres/${encodeURIComponent(genre)}`)
}

export async function getAlbum(id) {
  return apiCall(`/api/library/albums/${id}`)
}

export async function getTracks(page = 1, limit = 50) {
  return apiCall(`/api/library/tracks?page=${page}&limit=${limit}`)
}

export async function getTracksBatch(ids) {
  if (!ids || ids.length === 0) return {}
  return apiCall('/api/library/tracks/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ids.slice(0, 500))
  })
}

export async function search(query) {
  return apiCall(`/api/library/search?q=${encodeURIComponent(query)}`)
}

export async function updateAlbum(id, { title, year, genre }) {
  return apiCall(`/api/library/albums/${id}?title=${encodeURIComponent(title || '')}&year=${year || ''}&genre=${encodeURIComponent(genre || '')}`, {
    method: 'PUT'
  })
}

export async function updateTrack(id, { title, artist_name, album_title, track_number, disc_number }) {
  const params = new URLSearchParams()
  if (title !== undefined) params.append('title', title || '')
  if (artist_name !== undefined) params.append('artist_name', artist_name || '')
  if (album_title !== undefined) params.append('album_title', album_title || '')
  if (track_number !== undefined) params.append('track_number', track_number ?? '')
  if (disc_number !== undefined) params.append('disc_number', disc_number ?? '')
  return apiCall(`/api/library/tracks/${id}?${params.toString()}`, {
    method: 'PUT'
  })
}

export async function deleteAlbumArtwork(id) {
  return apiCall(`/api/library/albums/${id}/artwork`, {
    method: 'DELETE'
  })
}

// Playlists API
export async function getPlaylists() {
  return apiCall('/api/playlists')
}

export async function getPlaylist(id) {
  return apiCall(`/api/playlists/${id}`)
}

export async function createPlaylist(name, trackIds = []) {
  return apiCall('/api/playlists', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, track_ids: trackIds })
  })
}

export async function deletePlaylist(id) {
  return apiCall(`/api/playlists/${id}`, {
    method: 'DELETE'
  })
}

export async function addTrackToPlaylist(playlistId, trackId) {
  return apiCall(`/api/playlists/${playlistId}/tracks?track_id=${trackId}`, {
    method: 'POST'
  })
}

export async function getPlaylistDownloadTracks(playlistId) {
  return apiCall(`/api/playlists/${playlistId}/download/tracks`)
}

// Favorites API
export async function getFavorites() {
  return apiCall('/api/favorites')
}

export async function addFavorite(trackId) {
  return apiCall(`/api/favorites/${trackId}`, {
    method: 'POST'
  })
}

export async function removeFavorite(trackId) {
  return apiCall(`/api/favorites/${trackId}`, {
    method: 'DELETE'
  })
}

export async function checkFavorite(trackId) {
  return apiCall(`/api/favorites/check/${trackId}`)
}

// Config API
export async function getConfig() {
  return apiCall('/api/config')
}

export async function saveConfig(musicPath) {
  return apiCall('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ music_path: musicPath })
  })
}

// Users API
export async function getUsers() {
  return apiCall('/api/users')
}

export async function createUser(username, password, role = 'user') {
  return apiCall('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role })
  })
}

export async function deleteUser(id) {
  return apiCall(`/api/users/${id}`, {
    method: 'DELETE'
  })
}
