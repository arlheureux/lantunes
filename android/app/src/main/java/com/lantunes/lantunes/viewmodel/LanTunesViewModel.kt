package com.lantunes.lantunes.viewmodel

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import com.lantunes.lantunes.api.ApiClient
import com.lantunes.lantunes.api.WebSocketClient
import com.lantunes.lantunes.data.model.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class LanTunesViewModel(private val context: Context) : ViewModel() {
    
    private val apiClient = ApiClient.getInstance(context)
    private val wsClient = WebSocketClient(apiClient)
    private val gson = Gson()
    
    // Auth state
    val isLoggedIn = apiClient.tokenFlow.map { it != null }
    val serverUrl = apiClient.serverUrlFlow
    
    // User
    private val _currentUser = MutableStateFlow<User?>(null)
    val currentUser: StateFlow<User?> = _currentUser
    
    val isAdmin = _currentUser.map { it?.role == "admin" }
    
    // Library
    private val _albums = MutableStateFlow<List<Album>>(emptyList())
    val albums: StateFlow<List<Album>> = _albums
    
    private val _artists = MutableStateFlow<List<Artist>>(emptyList())
    val artists: StateFlow<List<Artist>> = _artists
    
    private val _tracks = MutableStateFlow<List<Track>>(emptyList())
    val tracks: StateFlow<List<Track>> = _tracks
    
    private val _playlists = MutableStateFlow<List<Playlist>>(emptyList())
    val playlists: StateFlow<List<Playlist>> = _playlists
    
    private val _searchResults = MutableStateFlow<LibraryResponse?>(null)
    val searchResults: StateFlow<LibraryResponse?> = _searchResults
    
    // Playback
    val playbackState = wsClient.playbackState
    val devices = wsClient.devices
    val queue = wsClient.queue
    val isConnected = wsClient.connectionState
    
    private val _selectedPlayerId = MutableStateFlow<String?>(null)
    val selectedPlayerId: StateFlow<String?> = _selectedPlayerId
    
    // UI State
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error
    
    private val _currentView = MutableStateFlow("library")
    val currentView: StateFlow<String> = _currentView
    
    // Users (admin)
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users
    
    // Config
    private val _config = MutableStateFlow<Map<String, Any>>(emptyMap())
    val config: StateFlow<Map<String, Any>> = _config
    
    init {
        viewModelScope.launch {
            apiClient.userFlow.collect { userJson ->
                _currentUser.value = userJson?.let {
                    try { gson.fromJson(it, User::class.java) } catch (e: Exception) { null }
                }
            }
        }
        
        viewModelScope.launch {
            wsClient.devices.collect { devs ->
                val player = devs.find { it.isPlayer }
                if (_selectedPlayerId.value == null && player != null) {
                    _selectedPlayerId.value = player.id
                }
            }
        }
    }
    
    fun setView(view: String) {
        _currentView.value = view
    }
    
    suspend fun checkAuthStatus(): Boolean {
        return try {
            val response = apiClient.api.authStatus()
            response.body()?.needsSetup == false
        } catch (e: Exception) {
            false
        }
    }
    
    suspend fun setup(username: String, password: String): Boolean {
        _isLoading.value = true
        return try {
            val response = apiClient.api.setup(LoginRequest(username, password))
            if (response.isSuccessful) {
                val body = response.body()!!
                apiClient.saveToken(body.accessToken)
                apiClient.saveUser(gson.toJson(body.user))
                connectWebSocket()
                true
            } else {
                _error.value = response.errorBody()?.string() ?: "Setup failed"
                false
            }
        } catch (e: Exception) {
            _error.value = e.message
            false
        } finally {
            _isLoading.value = false
        }
    }
    
    suspend fun login(username: String, password: String): Boolean {
        _isLoading.value = true
        return try {
            val response = apiClient.api.login(LoginRequest(username, password))
            if (response.isSuccessful) {
                val body = response.body()!!
                apiClient.saveToken(body.accessToken)
                apiClient.saveUser(gson.toJson(body.user))
                connectWebSocket()
                true
            } else {
                _error.value = "Invalid credentials"
                false
            }
        } catch (e: Exception) {
            _error.value = e.message
            false
        } finally {
            _isLoading.value = false
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            wsClient.disconnect()
            apiClient.clearSession()
            _currentUser.value = null
        }
    }
    
    private suspend fun connectWebSocket() {
        wsClient.connect()
    }
    
    suspend fun loadLibrary() {
        _isLoading.value = true
        try {
            val albumsRes = apiClient.api.getAlbums()
            if (albumsRes.isSuccessful) _albums.value = albumsRes.body() ?: emptyList()
            
            val artistsRes = apiClient.api.getArtists()
            if (artistsRes.isSuccessful) _artists.value = artistsRes.body() ?: emptyList()
            
            val tracksRes = apiClient.api.getTracks()
            if (tracksRes.isSuccessful) {
                _tracks.value = tracksRes.body()?.tracks ?: emptyList()
            }
            
            val playlistsRes = apiClient.api.getPlaylists()
            if (playlistsRes.isSuccessful) _playlists.value = playlistsRes.body() ?: emptyList()
        } catch (e: Exception) {
            _error.value = e.message
        } finally {
            _isLoading.value = false
        }
    }
    
    suspend fun search(query: String) {
        if (query.isBlank()) {
            _searchResults.value = null
            return
        }
        try {
            val response = apiClient.api.search(query)
            if (response.isSuccessful) _searchResults.value = response.body()
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun playTrack(track: Track) {
        try {
            val player = _selectedPlayerId.value
            val response = apiClient.api.play(trackId = track.id, player = player)
            if (response.isSuccessful) {
                // State will update via WebSocket
            }
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun play() {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.play(player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun pause() {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.pause(player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun next() {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.next(player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun previous() {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.previous(player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun seek(position: Int) {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.seek(position, player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun setVolume(volume: Double) {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.setVolume(volume, player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun toggleShuffle() {
        try {
            val player = _selectedPlayerId.value
            apiClient.api.toggleShuffle(player = player)
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    fun selectPlayer(deviceId: String) {
        _selectedPlayerId.value = deviceId
        wsClient.setPlayer(deviceId)
    }
    
    suspend fun loadUsers() {
        try {
            val response = apiClient.api.getUsers()
            if (response.isSuccessful) _users.value = response.body() ?: emptyList()
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun createUser(username: String, password: String, role: String): Boolean {
        try {
            val response = apiClient.api.createUser(CreateUserRequest(username, password, role))
            if (response.isSuccessful) {
                loadUsers()
                return true
            }
            _error.value = "Failed to create user"
            return false
        } catch (e: Exception) {
            _error.value = e.message
            return false
        }
    }
    
    suspend fun deleteUser(userId: Int): Boolean {
        try {
            val response = apiClient.api.deleteUser(userId)
            if (response.isSuccessful) {
                loadUsers()
                return true
            }
            return false
        } catch (e: Exception) {
            _error.value = e.message
            return false
        }
    }
    
    suspend fun loadConfig() {
        try {
            val response = apiClient.api.getConfig()
            if (response.isSuccessful) _config.value = response.body() ?: emptyMap()
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun saveConfig(newConfig: Map<String, Any>) {
        try {
            val response = apiClient.api.saveConfig(newConfig)
            if (response.isSuccessful) _config.value = newConfig
        } catch (e: Exception) {
            _error.value = e.message
        }
    }
    
    suspend fun scanLibrary(): String? {
        try {
            val response = apiClient.api.scanLibrary()
            return response.body()?.get("message")
        } catch (e: Exception) {
            return e.message
        }
    }
    
    suspend fun setServerUrl(url: String) {
        apiClient.saveServerUrl(url)
    }
    
    suspend fun getAlbumDetails(albumId: Int): AlbumDetails? {
        return try {
            val response = apiClient.api.getAlbum(albumId)
            if (response.isSuccessful) response.body() else null
        } catch (e: Exception) {
            _error.value = e.message
            null
        }
    }
    
    suspend fun getArtistDetails(artistId: Int): ArtistDetails? {
        return try {
            val response = apiClient.api.getArtist(artistId)
            if (response.isSuccessful) response.body() else null
        } catch (e: Exception) {
            _error.value = e.message
            null
        }
    }
    
    fun clearError() {
        _error.value = null
    }
    
    fun getStreamUrl(trackId: Int) = apiClient.getStreamUrl(trackId)
    fun getArtworkUrl(path: String?) = apiClient.getArtworkUrl(path)
    
    override fun onCleared() {
        super.onCleared()
        wsClient.disconnect()
    }
    
    class Factory(private val context: Context) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(LanTunesViewModel::class.java)) {
                return LanTunesViewModel(context) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}