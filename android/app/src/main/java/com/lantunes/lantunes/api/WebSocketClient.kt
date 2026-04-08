package com.lantunes.lantunes.api

import android.util.Log
import com.google.gson.Gson
import com.lantunes.lantunes.data.model.Device
import com.lantunes.lantunes.data.model.PlaybackState
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import okhttp3.*
import java.util.concurrent.TimeUnit

class WebSocketClient(private val apiClient: ApiClient) {
    
    private var webSocket: WebSocket? = null
    private val gson = Gson()
    
    private val _playbackState = MutableStateFlow<PlaybackState?>(null)
    val playbackState: StateFlow<PlaybackState?> = _playbackState
    
    private val _devices = MutableStateFlow<List<Device>>(emptyList())
    val devices: StateFlow<List<Device>> = _devices
    
    private val _queue = MutableStateFlow<List<Int>>(emptyList())
    val queue: StateFlow<List<Int>> = _queue
    
    private val _connectionState = MutableStateFlow(false)
    val connectionState: StateFlow<Boolean> = _connectionState
    
    private var deviceId: String = "android_${System.currentTimeMillis()}"
    private var deviceName: String = "Android Device"
    
    sealed class WebSocketMessage {
        data class PlaybackStateMessage(val state: PlaybackState) : WebSocketMessage()
        data class DevicesMessage(val devices: List<Device>) : WebSocketMessage()
        data class QueueUpdatedMessage(val queue: List<Int>) : WebSocketMessage()
    }
    
    private val _messages = Channel<WebSocketMessage>(Channel.BUFFERED)
    val messages = _messages.receiveAsFlow()
    
    fun setDeviceInfo(id: String, name: String) {
        deviceId = id
        deviceName = name
    }
    
    suspend fun connect() {
        val serverUrl = apiClient.getServerUrl() ?: return
        val wsUrl = serverUrl.replace("http", "ws") + "/ws"
        
        val client = OkHttpClient.Builder()
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .build()
        
        val request = Request.Builder()
            .url(wsUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d("WebSocket", "Connected")
                _connectionState.value = true
                register()
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val msg = gson.fromJson(text, Map::class.java)
                    val event = msg["event"] as? String
                    val data = msg["data"] as? Map<*, *>
                    
                    when (event) {
                        "playback_state" -> {
                            val stateJson = gson.toJson(data)
                            val state = gson.fromJson(stateJson, PlaybackState::class.java)
                            _playbackState.value = state
                            _messages.trySend(WebSocketMessage.PlaybackStateMessage(state))
                        }
                        "devices" -> {
                            val devicesJson = gson.toJson(data?.get("devices"))
                            val devs = gson.fromJson(devicesJson, Array<Device>::class.java).toList()
                            _devices.value = devs
                            _messages.trySend(WebSocketMessage.DevicesMessage(devs))
                        }
                        "queue_updated" -> {
                            val queueList = (data?.get("queue") as? List<*>)?.mapNotNull { it as? Int } ?: emptyList()
                            _queue.value = queueList
                            _messages.trySend(WebSocketMessage.QueueUpdatedMessage(queueList))
                        }
                    }
                } catch (e: Exception) {
                    Log.e("WebSocket", "Error parsing message: $e")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("WebSocket", "Error: ${t.message}")
                _connectionState.value = false
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d("WebSocket", "Closed: $reason")
                _connectionState.value = false
            }
        })
    }
    
    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        _connectionState.value = false
    }
    
    private fun register() {
        send("register", mapOf(
            "device_id" to deviceId,
            "device_name" to deviceName
        ))
    }
    
    fun setPlayer(deviceId: String) {
        send("set_player", mapOf("device_id" to deviceId))
    }
    
    fun updateDeviceName(name: String) {
        deviceName = name
        send("update_device_name", mapOf(
            "device_id" to deviceId,
            "device_name" to name
        ))
    }
    
    fun sendControl(action: String, position: Int? = null) {
        val data = mutableMapOf<String, Any>("action" to action)
        position?.let { data["position"] = it }
        send("control", data)
    }
    
    private fun send(event: String, data: Map<String, Any>) {
        val message = mapOf("event" to event, "data" to data)
        webSocket?.send(gson.toJson(message))
    }
}