package com.lantunes.lantunes.api

import com.lantunes.lantunes.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface LanTunesApi {
    
    // Auth
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>
    
    @POST("api/auth/setup")
    suspend fun setup(@Body request: LoginRequest): Response<LoginResponse>
    
    @GET("api/auth/status")
    suspend fun authStatus(): Response<AuthStatus>
    
    // Library
    @GET("api/library/albums")
    suspend fun getAlbums(): Response<List<Album>>
    
    @GET("api/library/artists")
    suspend fun getArtists(): Response<List<Artist>>
    
    @GET("api/library/tracks")
    suspend fun getTracks(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 50
    ): Response<LibraryResponse>
    
    @GET("api/library/search")
    suspend fun search(@Query("q") query: String): Response<LibraryResponse>
    
    @GET("api/library/albums/{id}")
    suspend fun getAlbum(@Path("id") id: Int): Response<AlbumDetails>
    
    @GET("api/library/artists/{id}")
    suspend fun getArtist(@Path("id") id: Int): Response<ArtistDetails>
    
    // Playback
    @GET("api/playback/state")
    suspend fun getPlaybackState(@Query("player") player: String?): Response<PlaybackState>
    
    @POST("api/playback/play")
    suspend fun play(
        @Query("track_id") trackId: Int? = null,
        @Query("player") player: String? = null
    ): Response<PlaybackState>
    
    @POST("api/playback/pause")
    suspend fun pause(@Query("player") player: String? = null): Response<PlaybackState>
    
    @POST("api/playback/next")
    suspend fun next(@Query("player") player: String? = null): Response<PlaybackState>
    
    @POST("api/playback/previous")
    suspend fun previous(@Query("player") player: String? = null): Response<PlaybackState>
    
    @POST("api/playback/seek")
    suspend fun seek(
        @Query("position") position: Int,
        @Query("player") player: String? = null
    ): Response<PlaybackState>
    
    @POST("api/playback/volume")
    suspend fun setVolume(
        @Query("volume") volume: Double,
        @Query("player") player: String? = null
    ): Response<PlaybackState>
    
    @POST("api/playback/shuffle")
    suspend fun toggleShuffle(@Query("player") player: String? = null): Response<PlaybackState>
    
    // Playlists
    @GET("api/playlists")
    suspend fun getPlaylists(): Response<List<Playlist>>
    
    // Users (admin)
    @GET("api/users")
    suspend fun getUsers(): Response<List<User>>
    
    @POST("api/users")
    suspend fun createUser(@Body request: CreateUserRequest): Response<User>
    
    @DELETE("api/users/{id}")
    suspend fun deleteUser(@Path("id") id: Int): Response<Unit>
    
    // Config
    @GET("api/config")
    suspend fun getConfig(): Response<Map<String, Any>>
    
    @POST("api/config")
    suspend fun saveConfig(@Body config: Map<String, Any>): Response<Unit>
    
    @POST("api/library/scan")
    suspend fun scanLibrary(): Response<Map<String, String>>
}