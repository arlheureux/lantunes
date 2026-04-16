package com.lantunes

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.os.IBinder
import android.os.StrictMode
import android.support.v4.media.session.MediaSessionCompat
import androidx.core.app.NotificationCompat
import androidx.media.app.NotificationCompat.MediaStyle
import java.net.URL

class PlaybackService : Service() {

    companion object {
        const val CHANNEL_ID = "lantunes_playback"
        const val NOTIFICATION_ID = 1
        const val ACTION_PLAY = "com.lantunes.PLAY"
        const val ACTION_PAUSE = "com.lantunes.PAUSE"
        const val ACTION_NEXT = "com.lantunes.NEXT"
        const val ACTION_PREV = "com.lantunes.PREV"
        const val ACTION_STOP = "com.lantunes.STOP"

        fun startService(context: Context) {
            val intent = Intent(context, PlaybackService::class.java).apply {
                action = ACTION_PLAY
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopService(context: Context) {
            val intent = Intent(context, PlaybackService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }

        fun updatePlaybackState(isPlaying: Boolean, trackTitle: String?, artistName: String?) {
            playbackState = PlaybackState(isPlaying, trackTitle, artistName)
        }

        fun setArtworkUrl(url: String) {
            artworkUrl = url
            artworkBitmap = null
        }

        data class PlaybackState(val isPlaying: Boolean, val trackTitle: String?, val artistName: String?)
        private var playbackState: PlaybackState? = null
        private var artworkUrl: String? = null
        private var artworkBitmap: Bitmap? = null
    }

    private lateinit var mediaSession: MediaSessionCompat

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        setupMediaSession()
    }

    private fun setupMediaSession() {
        mediaSession = MediaSessionCompat(this, "LanTunesMediaSession").apply {
            setCallback(mediaSessionCallback)
            isActive = true
        }
    }

    private val mediaSessionCallback = object : MediaSessionCompat.Callback() {
        override fun onPlay() {
            callJs("onPlay")
            updateNotificationState(true)
        }

        override fun onPause() {
            callJs("onPause")
            updateNotificationState(false)
        }

        override fun onSkipToNext() {
            callJs("onNext")
        }

        override fun onSkipToPrevious() {
            callJs("onPrevious")
        }

        override fun onStop() {
            callJs("onPause")
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private fun callJs(function: String) {
        try {
            MainActivity.webViewRef?.post {
                MainActivity.webViewRef?.evaluateJavascript("window.$function && window.$function()", null)
            }
        } catch (e: Exception) {
            // Ignore errors
        }
    }

    private fun updateNotificationState(isPlaying: Boolean) {
        val state = playbackState
        val title = state?.trackTitle ?: "LanTunes"
        val artist = state?.artistName ?: ""

        val notification = createNotification(title, artist, isPlaying)
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, notification)
    }

    private fun getArtworkBitmap(): Bitmap? {
        val url = artworkUrl ?: return null
        
        if (artworkBitmap != null) {
            return artworkBitmap
        }

        return try {
            val policy = StrictMode.ThreadPolicy.Builder().permitAll().build()
            StrictMode.setThreadPolicy(policy)
            
            val inputStream = URL(url).openStream()
            val bitmap = BitmapFactory.decodeStream(inputStream)
            inputStream.close()
            
            artworkBitmap = bitmap
            bitmap
        } catch (e: Exception) {
            null
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_PLAY -> {
                callJs("onPlay")
                startForeground(NOTIFICATION_ID, createNotification("Playing", "", true))
            }
            ACTION_PAUSE -> {
                callJs("onPause")
                updateNotificationState(false)
            }
            ACTION_NEXT -> callJs("onNext")
            ACTION_PREV -> callJs("onPrevious")
            ACTION_STOP -> {
                callJs("onPause")
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Playback",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "LanTunes playback controls"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(title: String, artist: String, isPlaying: Boolean): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val playPauseAction = if (isPlaying) {
            NotificationCompat.Action(
                android.R.drawable.ic_media_pause,
                "Pause",
                createPendingIntent(ACTION_PAUSE)
            )
        } else {
            NotificationCompat.Action(
                android.R.drawable.ic_media_play,
                "Play",
                createPendingIntent(ACTION_PLAY)
            )
        }

        val prevAction = NotificationCompat.Action(
            android.R.drawable.ic_media_previous,
            "Previous",
            createPendingIntent(ACTION_PREV)
        )

        val nextAction = NotificationCompat.Action(
            android.R.drawable.ic_media_next,
            "Next",
            createPendingIntent(ACTION_NEXT)
        )

        val style = MediaStyle()
            .setShowActionsInCompactView(0, 1, 2)
            .setMediaSession(mediaSession.sessionToken)

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(artist)
            .setSmallIcon(android.R.drawable.ic_media_play)
            .setContentIntent(pendingIntent)
            .setOngoing(isPlaying)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(prevAction)
            .addAction(playPauseAction)
            .addAction(nextAction)
            .setStyle(style)

        val artwork = getArtworkBitmap()
        if (artwork != null) {
            builder.setLargeIcon(artwork)
        }

        return builder.build()
    }

    private fun createPendingIntent(action: String): PendingIntent {
        val intent = Intent(this, PlaybackService::class.java).apply {
            this.action = action
        }
        return PendingIntent.getService(
            this,
            action.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    override fun onDestroy() {
        mediaSession.release()
        super.onDestroy()
    }
}
