package com.lantunes.lantunes.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lantunes.lantunes.data.model.AlbumDetails
import com.lantunes.lantunes.data.model.Track
import com.lantunes.lantunes.viewmodel.LanTunesViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AlbumScreen(
    albumId: Int,
    viewModel: LanTunesViewModel,
    onBack: () -> Unit,
    onPlayTrack: (Track) -> Unit
) {
    val albums by viewModel.albums.collectAsState()
    val album = albums.find { it.id == albumId }
    
    var albumDetails by remember { mutableStateOf<AlbumDetails?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    
    LaunchedEffect(albumId) {
        isLoading = true
        try {
            val response = viewModel.viewModelScope.launch {
                viewModel.viewModelScope.let { scope ->
                    val api = com.lantunes.lantunes.api.ApiClient.getInstance(
                        viewModel.viewModelScope.let { null as android.content.Context? }
                    )
                    // For now, use the albums list to show basic info
                }
            }
        } finally {
            isLoading = false
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(album?.title ?: "Album") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    albumDetails?.let { details ->
                        IconButton(
                            onClick = {
                                details.tracks?.firstOrNull()?.let { track ->
                                    viewModel.viewModelScope.launch { viewModel.playTrack(track) }
                                }
                            }
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
                        modifier = Modifier
                            .size(200.dp)
                    ) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.Album,
                                contentDescription = null,
                                modifier = Modifier.size(100.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text(
                        text = album?.title ?: "",
                        style = MaterialTheme.typography.headlineSmall
                    )
                    
                    album?.artistId?.let { artistId ->
                        val artists by viewModel.artists.collectAsState()
                        val artist = artists.find { it.id == artistId }
                        Text(
                            text = artist?.name ?: "Unknown Artist",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    
                    album?.year?.let { year ->
                        Text(
                            text = year.toString(),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            val tracks by viewModel.tracks.collectAsState()
            val albumTracks = tracks.filter { it.albumId == albumId }.sortedBy { it.trackNumber }
            
            items(albumTracks) { track ->
                ListItem(
                    headlineContent = {
                        Text(
                            track.title,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    },
                    supportingContent = {
                        Row {
                            track.trackNumber?.let { Text("$it. ") }
                            Text(track.durationFormatted)
                        }
                    },
                    trailingContent = {
                        IconButton(
                            onClick = { viewModel.viewModelScope.launch { viewModel.playTrack(track) } }
                        ) {
                            Icon(Icons.Default.PlayArrow, contentDescription = "Play")
                        }
                    },
                    modifier = Modifier.clickable { viewModel.viewModelScope.launch { viewModel.playTrack(track) } }
                )
            }
        }
    }
}