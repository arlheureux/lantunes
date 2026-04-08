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
import androidx.compose.ui.unit.dp
import com.lantunes.lantunes.data.model.User
import com.lantunes.lantunes.viewmodel.LanTunesViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: LanTunesViewModel,
    onBack: () -> Unit,
    onLogout: () -> Unit
) {
    val serverUrl by viewModel.serverUrl.collectAsState(initial = "")
    val currentUser by viewModel.currentUser.collectAsState()
    val isAdmin by viewModel.isAdmin.collectAsState(initial = false)
    val users by viewModel.users.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    
    var showServerUrlDialog by remember { mutableStateOf(false) }
    var showCreateUserDialog by remember { mutableStateOf(false) }
    var showDeleteUserDialog by remember { mutableStateOf(false) }
    var userToDelete by remember { mutableStateOf<User?>(null) }
    
    LaunchedEffect(isAdmin) {
        if (isAdmin) viewModel.loadUsers()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
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
                ListItem(
                    headlineContent = { Text("Server URL") },
                    supportingContent = { Text(serverUrl) },
                    leadingContent = { Icon(Icons.Default.Cloud, contentDescription = null) },
                    trailingContent = {
                        IconButton(onClick = { showServerUrlDialog = true }) {
                            Icon(Icons.Default.Edit, contentDescription = "Edit")
                        }
                    }
                )
            }
            
            item { HorizontalDivider() }
            
            item {
                ListItem(
                    headlineContent = { Text("Account") },
                    supportingContent = { Text("${currentUser?.username} (${currentUser?.role})") },
                    leadingContent = { Icon(Icons.Default.Person, contentDescription = null) }
                )
            }
            
            item { HorizontalDivider() }
            
            if (isAdmin) {
                item {
                    ListItem(
                        headlineContent = { Text("User Management") },
                        supportingContent = { Text("${users.size} users") },
                        leadingContent = { Icon(Icons.Default.AdminPanelSettings, contentDescription = null) },
                        trailingContent = {
                            IconButton(onClick = { showCreateUserDialog = true }) {
                                Icon(Icons.Default.Add, contentDescription = "Add User")
                            }
                        }
                    )
                }
                
                items(users) { user ->
                    ListItem(
                        headlineContent = { Text(user.username) },
                        supportingContent = { Text("${user.role} - ${user.status}") },
                        trailingContent = {
                            if (user.id != currentUser?.id) {
                                IconButton(onClick = { userToDelete = user; showDeleteUserDialog = true }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Delete")
                                }
                            }
                        }
                    )
                }
                
                item { HorizontalDivider() }
            }
            
            item {
                ListItem(
                    headlineContent = { Text("Logout") },
                    leadingContent = { Icon(Icons.Default.Logout, contentDescription = null) },
                    modifier = Modifier.clickable(onClick = onLogout)
                )
            }
        }
    }
    
    if (showServerUrlDialog) {
        var newUrl by remember { mutableStateOf(serverUrl) }
        AlertDialog(
            onDismissRequest = { showServerUrlDialog = false },
            title = { Text("Server URL") },
            text = {
                OutlinedTextField(
                    value = newUrl,
                    onValueChange = { newUrl = it },
                    label = { Text("URL") },
                    singleLine = true
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.viewModelScope.launch { viewModel.setServerUrl(newUrl) }
                    showServerUrlDialog = false
                }) {
                    Text("Save")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerUrlDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
    
    if (showCreateUserDialog) {
        var username by remember { mutableStateOf("") }
        var password by remember { mutableStateOf("") }
        var role by remember { mutableStateOf("user") }
        
        AlertDialog(
            onDismissRequest = { showCreateUserDialog = false },
            title = { Text("Create User") },
            text = {
                Column {
                    OutlinedTextField(
                        value = username,
                        onValueChange = { username = it },
                        label = { Text("Username") },
                        singleLine = true
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        label = { Text("Password") },
                        singleLine = true
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = role == "user",
                            onClick = { role = "user" }
                        )
                        Text("User")
                        Spacer(modifier = Modifier.width(16.dp))
                        RadioButton(
                            selected = role == "admin",
                            onClick = { role = "admin" }
                        )
                        Text("Admin")
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.viewModelScope.launch {
                            viewModel.createUser(username, password, role)
                        }
                        showCreateUserDialog = false
                    },
                    enabled = username.isNotBlank() && password.isNotBlank()
                ) {
                    Text("Create")
                }
            },
            dismissButton = {
                TextButton(onClick = { showCreateUserDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
    
    if (showDeleteUserDialog && userToDelete != null) {
        AlertDialog(
            onDismissRequest = { showDeleteUserDialog = false },
            title = { Text("Delete User") },
            text = { Text("Are you sure you want to delete ${userToDelete?.username}?") },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.viewModelScope.launch {
                        userToDelete?.let { viewModel.deleteUser(it.id) }
                    }
                    showDeleteUserDialog = false
                }) {
                    Text("Delete")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteUserDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

private fun Modifier.clickable(onClick: () -> Unit): Modifier = this