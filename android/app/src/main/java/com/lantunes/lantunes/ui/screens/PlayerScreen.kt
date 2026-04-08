package com.lantunes.lantunes.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.lantunes.lantunes.data.model.Device
import com.lantunes.lantunes.data.model.PlaybackState
import com.lantunes.lantunes.viewmodel.LanTunesViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlayerScreen(
    viewModel: LanTunesViewModel,
    onBack: () -> Unit
) {
    val playbackState by viewModel.playbackState.collectAsState()
    val devices by viewModel.devices.collectAsState()
    val selectedPlayerId by viewModel.selectedPlayerId.collectAsState()
    val isAdmin by viewModel.isAdmin.collectAsState(initial = false)
    val users by viewModel.users.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Now Playing") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        if (playbackState?.track == null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No track playing",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Album art placeholder
                Card(
                    modifier = Modifier
                        .fillMaxWidth(0.8f)
                        .aspectRatio(1f)
                ) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            Icons.Default.MusicNote,
                            contentDescription = null,
                            modifier = Modifier.size(120.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(32.dp))
                
                // Track info
                Text(
                    text = playbackState!!.track!!.title,
                    style = MaterialTheme.typography.headlineSmall,
                    textAlign = TextAlign.Center,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "Artist",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Spacer(modifier = Modifier.height(32.dp))
                
                // Progress
                val progress = if (playbackState!!.track!!.duration != null && playbackState!!.track!!.duration!! > 0) {
                    playbackState!!.position.toFloat() / playbackState!!.track!!.duration!!.toFloat()
                } else 0f
                
                Slider(
                    value = progress,
                    onValueChange = { value ->
                        val newPosition = (value * (playbackState!!.track!!.duration ?: 0)).toInt()
                        viewModel.viewModelScope.launch { viewModel.seek(newPosition) }
                    },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(formatDuration(playbackState!!.position))
                    Text(formatDuration(playbackState!!.track!!.duration ?: 0))
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Controls
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(
                        onClick = { viewModel.viewModelScope.launch { viewModel.toggleShuffle() } }
                    ) {
                        Icon(
                            Icons.Default.Shuffle,
                            contentDescription = "Shuffle",
                            tint = if (playbackState!!.shuffleMode) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    
                    IconButton(
                        onClick = { viewModel.viewModelScope.launch { viewModel.previous() } }
                    ) {
                        Icon(Icons.Default.SkipPrevious, contentDescription = "Previous", modifier = Modifier.size(36.dp))
                    }
                    
                    FilledIconButton(
                        onClick = {
                            if (playbackState!!.isPlaying) viewModel.viewModelScope.launch { viewModel.pause() }
                            else viewModel.viewModelScope.launch { viewModel.play() }
                        },
                        modifier = Modifier.size(72.dp)
                    ) {
                        Icon(
                            if (playbackState!!.isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                            contentDescription = if (playbackState!!.isPlaying) "Pause" else "Play",
                            modifier = Modifier.size(48.dp)
                        )
                    }
                    
                    IconButton(
                        onClick = { viewModel.viewModelScope.launch { viewModel.next() } }
                    ) {
                        Icon(Icons.Default.SkipNext, contentDescription = "Next", modifier = Modifier.size(36.dp))
                    }
                    
                    IconButton(onClick = {}) {
                        Icon(Icons.Default.VolumeUp, contentDescription = "Volume")
                    }
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // Device selector
                if (devices.isNotEmpty()) {
                    Text(
                        text = "Playing on:",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    LazyColumn {
                        items(devices) { device ->
                            ListItem(
                                headlineContent = { Text(device.name) },
                                leadingContent = {
                                    RadioButton(
                                        selected = device.id == selectedPlayerId,
                                        onClick = { viewModel.selectPlayer(device.id) }
                                    )
                                },
                                trailingContent = {
                                    if (device.isPlayer) Text("Playing", color = MaterialTheme.colorScheme.primary)
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun formatDuration(seconds: Int): String {
    val minutes = seconds / 60
    val secs = seconds % 60
    return "$minutes:${secs.toString().padStart(2, '0')}"
}