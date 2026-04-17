import { ref } from 'vue'

const toasts = ref([])

export function useToast() {
  function show(message, type = 'info', duration = 3000) {
    const id = Date.now()
    toasts.value.push({ id, message, type })

    setTimeout(() => {
      remove(id)
    }, duration)

    return id
  }

  function remove(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  function success(message) {
    return show(message, 'success')
  }

  function error(message) {
    return show(message, 'error')
  }

  function info(message) {
    return show(message, 'info')
  }

  return {
    toasts,
    show,
    remove,
    success,
    error,
    info
  }
}
