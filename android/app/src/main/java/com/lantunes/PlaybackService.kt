package com.lantunes

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder

class PlaybackService : Service() {

    companion object {
        const val CHANNEL_ID = "lantunes_playback"
        const val NOTIFICATION_ID = 1

        fun start(context: Context) {
            try {
                val intent = Intent(context, PlaybackService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (e: Exception) {
                // Ignore
            }
        }

        fun stop(context: Context) {
            try {
                val intent = Intent(context, PlaybackService::class.java)
                context.stopService(intent)
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createChannel()
        startForeground(NOTIFICATION_ID, createNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                val channel = NotificationChannel(CHANNEL_ID, "Playback", NotificationManager.IMPORTANCE_LOW)
                channel.description = "LanTunes"
                val manager = getSystemService(NotificationManager::class.java)
                manager.createNotificationChannel(channel)
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    private fun createNotification(): Notification {
        return try {
            val intent = Intent(this, MainActivity::class.java)
            val pending = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)
            
            Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("LanTunes")
                .setContentText("Playing")
                .setSmallIcon(android.R.drawable.ic_media_play)
                .setContentIntent(pending)
                .setOngoing(true)
                .build()
        } catch (e: Exception) {
            Notification()
        }
    }
}