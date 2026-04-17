import { ref, computed } from 'vue'

export function usePlayer() {
  const playbackState = ref({
    track: null,
    position: 0,
    is_playing: false,
    volume: 1.0,
    queue: [],
    queue_index: 0,
    shuffle_mode: false,
    repeat_mode: 'off',
    player_device_id: null
  })

  const isLiked = ref(false)
  const isLoading = ref(false)

  const progressPercent = computed(() => {
    if (!playbackState.value.track?.duration) return 0
    return (playbackState.value.position / playbackState.value.track.duration) * 100
  })

  function updateState(newState) {
    playbackState.value = { ...playbackState.value, ...newState }
  }

  function updatePosition(position) {
    playbackState.value.position = position
  }

  function updateQueue(queue) {
    playbackState.value.queue = queue
  }

  function setVolume(volume) {
    playbackState.value.volume = volume
  }

  function setLiked(value) {
    isLiked.value = value
  }

  function setLoading(value) {
    isLoading.value = value
  }

  return {
    playbackState,
    isLiked,
    isLoading,
    progressPercent,
    updateState,
    updatePosition,
    updateQueue,
    setVolume,
    setLiked,
    setLoading
  }
}
