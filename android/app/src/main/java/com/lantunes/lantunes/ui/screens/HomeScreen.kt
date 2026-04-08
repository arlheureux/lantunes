package com.lantunes.lantunes.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lantunes.lantunes.data.model.Album
import com.lantunes.lantunes.data.model.Artist
import com.lantunes.lantunes.data.model.Track
import com.lantunes.lantunes.viewmodel.LanTunesViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: LanTunesViewModel,
    onNavigateToAlbum: (Int) -> Unit,
    onNavigateToArtist: (Int) -> Unit,
    onNavigateToPlayer: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val albums by viewModel.albums.collectAsState()
    val artists by viewModel.artists.collectAsState()
    val tracks by viewModel.tracks.collectAsState()
    val playlists by viewModel.playlists.collectAsState()
    val playbackState by viewModel.playbackState.collectAsState()
    val devices by viewModel.devices.collectAsState()
    val selectedPlayerId by viewModel.selectedPlayerId.collectAsState()
    val currentView by viewModel.currentView.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val searchResults by viewModel.searchResults.collectAsState()
    
    var searchQuery by remember { mutableStateOf("") }
    var selectedTab by remember { mutableIntStateOf(0) }
    
    LaunchedEffect(Unit) {
        viewModel.loadLibrary()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("LanTunes") },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        },
        bottomBar = {
            playbackState.track?.let { track ->
                MiniPlayer(
                    track = track,
                    isPlaying = playbackState.isPlaying,
                    onPlayPause = {
                        if (playbackState.isPlaying) viewModel.pause() else viewModel.play()
                    },
                    onClick = onNavigateToPlayer
                )
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Search
            OutlinedTextField(
                value = searchQuery,
                onValueChange = {
                    searchQuery = it
                    viewModel.viewModelScope.launch { viewModel.search(it) }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                placeholder = { Text("Search") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                singleLine = true
            )
            
            // Show search results or tabs
            if (searchQuery.isNotEmpty() && searchResults != null) {
                SearchResultsContent(
                    results = searchResults,
                    viewModel = viewModel,
                    onPlayTrack = { viewModel.viewModelScope.launch { viewModel.playTrack(it) } },
                    onAlbumClick = onNavigateToAlbum,
                    onArtistClick = onNavigateToArtist
                )
            } else {
                // Tabs
                TabRow(selectedTabIndex = selectedTab) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 },
                        text = { Text("Albums") }
                    )
                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 },
                        text = { Text("Artists") }
                    )
                    Tab(
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2 },
                        text = { Text("Tracks") }
                    )
                    Tab(
                        selected = selectedTab == 3,
                        onClick = { selectedTab = 3 },
                        text = { Text("Playlists") }
                    )
                }
                
                when (selectedTab) {
                    0 -> AlbumsGrid(albums = albums, onAlbumClick = onNavigateToAlbum)
                    1 -> ArtistsList(artists = artists, onArtistClick = onNavigateToArtist)
                    2 -> TracksList(
                        tracks = tracks,
                        onTrackClick = { viewModel.viewModelScope.launch { viewModel.playTrack(it) } }
                    )
                    3 -> PlaylistsList(playlists = playlists)
                }
            }
        }
    }
}

@Composable
fun AlbumsGrid(albums: List<Album>, onAlbumClick: (Int) -> Unit) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(albums) { album ->
            AlbumCard(album = album, onClick = { onAlbumClick(album.id) })
        }
    }
}

@Composable
fun AlbumCard(album: Album, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1f)
            .clickable(onClick = onClick)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.Album,
                    contentDescription = null,
                    modifier = Modifier.size(64.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Text(
                text = album.title,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(8.dp)
            )
        }
    }
}

@Composable
fun ArtistsList(artists: List<Artist>, onArtistClick: (Int) -> Unit) {
    LazyColumn {
        items(artists) { artist ->
            ListItem(
                headlineContent = { Text(artist.name) },
                leadingContent = {
                    Icon(Icons.Default.Person, contentDescription = null)
                },
                modifier = Modifier.clickable { onArtistClick(artist.id) }
            )
        }
    }
}

@Composable
fun TracksList(tracks: List<Track>, onTrackClick: (Track) -> Unit) {
    LazyColumn {
        items(tracks) { track ->
            ListItem(
                headlineContent = { Text(track.title, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                supportingContent = { Text(track.durationFormatted) },
                trailingContent = {
                    Icon(Icons.Default.PlayArrow, contentDescription = "Play")
                },
                modifier = Modifier.clickable { onTrackClick(track) }
            )
        }
    }
}

@Composable
fun PlaylistsList(playlists: List<com.lantunes.lantunes.data.model.Playlist>) {
    LazyColumn {
        items(playlists) { playlist ->
            ListItem(
                headlineContent = { Text(playlist.name) },
                supportingContent = { Text("${playlist.trackCount ?: 0} tracks") },
                leadingContent = {
                    Icon(Icons.Default.QueueMusic, contentDescription = null)
                }
            )
        }
    }
}

@Composable
fun SearchResultsContent(
    results: com.lantunes.lantunes.data.model.LibraryResponse?,
    viewModel: LanTunesViewModel,
    onPlayTrack: (Track) -> Unit,
    onAlbumClick: (Int) -> Unit,
    onArtistClick: (Int) -> Unit
) {
    LazyColumn {
        results?.tracks?.let { tracks ->
            items(tracks) { track ->
                ListItem(
                    headlineContent = { Text(track.title) },
                    trailingContent = { Icon(Icons.Default.PlayArrow, contentDescription = null) },
                    modifier = Modifier.clickable { onPlayTrack(track) }
                )
            }
        }
        results?.albums?.let { albums ->
            items(albums) { album ->
                ListItem(
                    headlineContent = { Text(album.title) },
                    leadingContent = { Icon(Icons.Default.Album, contentDescription = null) },
                    modifier = Modifier.clickable { onAlbumClick(album.id) }
                )
            }
        }
        results?.artists?.let { artists ->
            items(artists) { artist ->
                ListItem(
                    headlineContent = { Text(artist.name) },
                    leadingContent = { Icon(Icons.Default.Person, contentDescription = null) },
                    modifier = Modifier.clickable { onArtistClick(artist.id) }
                )
            }
        }
    }
}

@Composable
fun MiniPlayer(
    track: com.lantunes.lantunes.data.model.Track,
    isPlaying: Boolean,
    onPlayPause: () -> Unit,
    onClick: () -> Unit
) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.MusicNote,
                contentDescription = null,
                modifier = Modifier.size(48.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = track.title,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f)
            )
            IconButton(onClick = onPlayPause) {
                Icon(
                    if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                    contentDescription = if (isPlaying) "Pause" else "Play"
                )
            }
        }
    }
}