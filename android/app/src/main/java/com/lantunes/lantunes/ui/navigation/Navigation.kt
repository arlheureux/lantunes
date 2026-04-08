package com.lantunes.lantunes.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.lifecycle.viewmodel.compose.viewModel
import android.content.Context
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.lantunes.lantunes.ui.screens.*
import com.lantunes.lantunes.viewmodel.LanTunesViewModel

sealed class Screen(val route: String) {
    object Setup : Screen("setup")
    object Login : Screen("login")
    object Home : Screen("home")
    object Player : Screen("player")
    object Settings : Screen("settings")
    object Album : Screen("album/{albumId}") {
        fun createRoute(albumId: Int) = "album/$albumId"
    }
    object Artist : Screen("artist/{artistId}") {
        fun createRoute(artistId: Int) = "artist/$artistId"
    }
}

@Composable
fun LanTunesNavHost() {
    val navController = rememberNavController()
    val context = navController.context
    val viewModel: LanTunesViewModel = viewModel(factory = LanTunesViewModel.Factory(context))
    
    val isLoggedIn by viewModel.isLoggedIn.collectAsState(initial = false)
    val isLoading by viewModel.isLoading.collectAsState(initial = true)
    
    val startDestination = if (isLoggedIn) Screen.Home.route else Screen.Login.route
    
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                viewModel = viewModel,
                onLoginSuccess = { navController.navigate(Screen.Home.route) { popUpTo(Screen.Login.route) { inclusive = true } } }
            )
        }
        
        composable(Screen.Setup.route) {
            SetupScreen(
                viewModel = viewModel,
                onSetupComplete = { navController.navigate(Screen.Home.route) { popUpTo(Screen.Setup.route) { inclusive = true } } }
            )
        }
        
        composable(Screen.Home.route) {
            HomeScreen(
                viewModel = viewModel,
                onNavigateToAlbum = { albumId -> navController.navigate(Screen.Album.createRoute(albumId)) },
                onNavigateToArtist = { artistId -> navController.navigate(Screen.Artist.createRoute(artistId)) },
                onNavigateToPlayer = { navController.navigate(Screen.Player.route) },
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }
        
        composable(Screen.Player.route) {
            PlayerScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
        
        composable(Screen.Settings.route) {
            SettingsScreen(
                viewModel = viewModel,
                onBack = { navController.popBackStack() },
                onLogout = {
                    viewModel.logout()
                    navController.navigate(Screen.Login.route) { popUpTo(0) { inclusive = true } }
                }
            )
        }
        
        composable(
            route = Screen.Album.route,
            arguments = listOf(navArgument("albumId") { type = NavType.IntType })
        ) { backStackEntry ->
            val albumId = backStackEntry.arguments?.getInt("albumId") ?: 0
            AlbumScreen(
                albumId = albumId,
                viewModel = viewModel,
                onBack = { navController.popBackStack() },
                onPlayTrack = { /* Already handled in screen */ }
            )
        }
        
        composable(
            route = Screen.Artist.route,
            arguments = listOf(navArgument("artistId") { type = NavType.IntType })
        ) { backStackEntry ->
            val artistId = backStackEntry.arguments?.getInt("artistId") ?: 0
            ArtistScreen(
                artistId = artistId,
                viewModel = viewModel,
                onBack = { navController.popBackStack() }
            )
        }
    }
}