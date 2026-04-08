package com.lantunes.lantunes.data.model

import com.google.gson.annotations.SerializedName

data class Album(
    val id: Int,
    val title: String,
    @SerializedName("artist_id") val artistId: Int?,
    val year: Int?,
    val genre: String?,
    @SerializedName("artwork_path") val artworkPath: String?
)

data class Artist(
    val id: Int,
    val name: String,
    @SerializedName("sort_name") val sortName: String?,
    @SerializedName("artwork_path") val artworkPath: String?
)

data class Track(
    val id: Int,
    val title: String,
    @SerializedName("album_id") val albumId: Int?,
    @SerializedName("artist_id") val artistId: Int?,
    @SerializedName("disc_number") val discNumber: Int?,
    @SerializedName("track_number") val trackNumber: Int?,
    val duration: Int?,
    val path: String?,
    @SerializedName("file_format") val fileFormat: String?,
    @SerializedName("stream_url") val streamUrl: String?
) {
    val durationFormatted: String
        get() {
            if (duration == null) return "0:00"
            val minutes = duration / 60
            val seconds = duration % 60
            return "$minutes:${seconds.toString().padStart(2, '0')}"
        }
}

data class Playlist(
    val id: Int,
    val name: String,
    @SerializedName("track_count") val trackCount: Int?
)

data class User(
    val id: Int,
    val username: String,
    val role: String,
    val status: String
)

data class Device(
    val id: String,
    val name: String,
    @SerializedName("is_player") val isPlayer: Boolean
)

data class PlaybackState(
    val track: Track?,
    val position: Int,
    @SerializedName("is_playing") val isPlaying: Boolean,
    val volume: Double,
    val queue: List<Int>,
    @SerializedName("queue_index") val queueIndex: Int,
    @SerializedName("shuffle_mode") val shuffleMode: Boolean,
    @SerializedName("player_device_id") val playerDeviceId: String?
)

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: User
)

data class AuthStatus(
    @SerializedName("needs_setup") val needsSetup: Boolean
)

data class CreateUserRequest(
    val username: String,
    val password: String,
    val role: String = "user"
)

data class LibraryResponse(
    val tracks: List<Track>?,
    val albums: List<Album>?,
    val artists: List<Artist>?,
    val playlists: List<Playlist>?,
    val total: Int?,
    val pages: Int?
)

data class AlbumDetails(
    val id: Int,
    val title: String,
    @SerializedName("artist_id") val artistId: Int?,
    val year: Int?,
    val genre: String?,
    @SerializedName("artwork_path") val artworkPath: String?,
    val tracks: List<Track>?,
    val artist: Artist?
)

data class ArtistDetails(
    val id: Int,
    val name: String,
    @SerializedName("artwork_path") val artworkPath: String?,
    val albums: List<Album>?,
    val tracks: List<Track>?
)