import { ref, computed } from 'vue'
import { useWebSocket } from './useWebSocket.js'

export function usePlayer() {
  const currentTrack = ref(null)
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(1.0)
  const muted = ref(false)
  const shuffle = ref(false)
  const repeat = ref('none')
  const queue = ref([])
  const queueIndex = ref(0)
  const isLoading = ref(false)

  const { send } = useWebSocket()

  const hasCurrentTrack = computed(() => !!currentTrack.value)

  function play(track, index = 0) {
    if (track) {
      currentTrack.value = track
      isPlaying.value = true
      send('play', { track_id: track.id })
    }
  }

  function pause() {
    isPlaying.value = false
    send('pause')
  }

  function previous() {
    if (queueIndex.value > 0) {
      queueIndex.value--
      currentTrack.value = queue.value[queueIndex.value]
      play(currentTrack.value)
    }
  }

  function next() {
    if (queueIndex.value < queue.value.length - 1) {
      queueIndex.value++
      currentTrack.value = queue.value[queueIndex.value]
      play(currentTrack.value)
    }
  }

  function seek(position) {
    currentTime.value = position
    send('seek', { position })
  }

  function setVolume(vol) {
    volume.value = vol
    send('volume', { volume: vol })
  }

  function toggleMute() {
    muted.value = !muted.value
  }

  function setShuffle(value) {
    shuffle.value = value
  }

  function setRepeat(value) {
    repeat.value = value
  }

  function updateState(state) {
    if (state.track) currentTrack.value = state.track
    if (state.is_playing !== undefined) isPlaying.value = state.is_playing
    if (state.position !== undefined) currentTime.value = state.position
    if (state.volume !== undefined) volume.value = state.volume
    if (state.queue) queue.value = state.queue
    if (state.queue_index !== undefined) queueIndex.value = state.queue_index
  }

  function playTrack(track) {
    queue.value = [track]
    queueIndex.value = 0
    play(track)
  }

  return {
    currentTrack,
    isPlaying,
    currentTime,
    duration,
    volume,
    muted,
    shuffle,
    repeat,
    queue,
    queueIndex,
    isLoading,
    hasCurrentTrack,
    play,
    pause,
    previous,
    next,
    seek,
    setVolume,
    toggleMute,
    setShuffle,
    setRepeat,
    updateState,
    playTrack
  }
}
