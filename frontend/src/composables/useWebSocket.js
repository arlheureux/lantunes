import { ref, onMounted, onUnmounted } from 'vue'
import { getMediaUrl } from '../api/index.js'

let ws = null
let reconnectAttempts = 0
const maxReconnectAttempts = 10

export function useWebSocket() {
  const sessions = ref([])
  const isConnected = ref(false)

  let messageHandlers = []
  let onStateChange = null
  let onQueueChange = null
  let onPositionChange = null
  let onSessionsChange = null

  function setHandlers({ onState, onQueue, onPosition, onSessions }) {
    onStateChange = onState
    onQueueChange = onQueue
    onPositionChange = onPosition
    onSessionsChange = onSessions
  }

  function connect() {
    const token = localStorage.getItem('access_token')
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = token
      ? `${wsProtocol}//${location.host}/ws?token=${encodeURIComponent(token)}`
      : `${wsProtocol}//${location.host}/ws`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
      registerDevice()
    }

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      switch (msg.event) {
        case 'playback_state':
          if (onStateChange) onStateChange(msg.data)
          break
        case 'queue_updated':
          if (onQueueChange) onQueueChange(msg.data.queue || [])
          break
        case 'position_update':
          if (onPositionChange) onPositionChange(msg.data.position)
          break
        case 'sessions':
          sessions.value = msg.data.sessions || []
          if (onSessionsChange) onSessionsChange(sessions.value)
          break
      }
    }

    ws.onerror = (e) => {
      console.error('WebSocket error:', e)
    }

    ws.onclose = () => {
      isConnected.value = false
      if (reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
        reconnectAttempts++
        setTimeout(connect, delay)
      }
    }
  }

  function send(event, data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ event, data }))
    }
  }

  function registerDevice() {
    const sessionId = getOrCreateSessionId()
    const deviceId = getOrCreateDeviceId()
    const deviceName = localStorage.getItem('lantunes_device_name') || 'My Device'
    send('register', { session_id: sessionId, device_id: deviceId, device_name: deviceName })
  }

  function getOrCreateSessionId() {
    let sessionId = localStorage.getItem('lantunes_session_id')
    if (!sessionId) {
      sessionId = 'session_' + Math.random().toString(36).substr(2, 9)
      localStorage.setItem('lantunes_session_id', sessionId)
    }
    return sessionId
  }

  function getOrCreateDeviceId() {
    let deviceId = localStorage.getItem('lantunes_device_id')
    if (!deviceId) {
      deviceId = 'device_' + Math.random().toString(36).substr(2, 9)
      localStorage.setItem('lantunes_device_id', deviceId)
    }
    return deviceId
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    sessions,
    isConnected,
    connect,
    disconnect,
    send,
    setHandlers,
    getSessionId: getOrCreateSessionId,
    getDeviceId: getOrCreateDeviceId
  }
}
