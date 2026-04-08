package com.lantunes.lantunes.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import com.lantunes.lantunes.data.model.Track
import com.lantunes.lantunes.viewmodel.LanTunesViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArtistScreen(
    artistId: Int,
    viewModel: LanTunesViewModel,
    onBack: () -> Unit
) {
    val artists by viewModel.artists.collectAsState()
    val artist = artists.find { it.id == artistId }
    
    val albums by viewModel.albums.collectAsState()
    val artistAlbums = albums.filter { it.artistId == artistId }
    
    val tracks by viewModel.tracks.collectAsState()
    val artistTracks = tracks.filter { it.artistId == artistId }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(artist?.name ?: "Artist") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    artistTracks.firstOrNull()?.let { track ->
                        IconButton(
                            onClick = { viewModel.viewModelScope.launch { viewModel.playTrack(track) } }
                        ) {
                            Icon(Icons.Default.PlayArrow, contentDescription = "Play All")
                        }
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            item {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Card(
                        modifier = Modifier.size(150.dp)
                    ) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.Person,
                                contentDescription = null,
                                modifier = Modifier.size(80.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text(
                        text = artist?.name ?: "",
                        style = MaterialTheme.typography.headlineSmall
                    )
                    
                    Text(
                        text = "${artistAlbums.size} albums, ${artistTracks.size} tracks",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            if (artistAlbums.isNotEmpty()) {
                item {
                    Text(
                        text = "Albums",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
                
                item {
                    LazyRow(
                        contentPadding = PaddingValues(horizontal = 16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(artistAlbums) { album ->
                            AlbumItem(album = album, onClick = {})
                        }
                    }
                }
            }
            
            if (artistTracks.isNotEmpty()) {
                item {
                    Text(
                        text = "Tracks",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
                
                items(artistTracks) { track ->
                    ListItem(
                        headlineContent = {
                            Text(
                                track.title,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        },
                        supportingContent = {
                            track.albumId?.let { albumId ->
                                val album = albums.find { it.id == albumId }
                                Text(album?.title ?: "")
                            }
                        },
                        trailingContent = {
                            Text(track.durationFormatted)
                        },
                        modifier = Modifier.clickable { viewModel.viewModelScope.launch { viewModel.playTrack(track) } }
                    )
                }
            }
        }
    }
}

@Composable
private fun AlbumItem(album: Album, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .width(140.dp)
            .clickable(onClick = onClick)
    ) {
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.Album,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Text(
                text = album.title,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(8.dp)
            )
        }
    }
}