<template>
  <Teleport to="body">
    <div v-if="visible" class="context-menu-backdrop" @click="close" @contextmenu.prevent="close">
      <div
        ref="menuRef"
        class="context-menu"
        :style="menuStyle"
        @click.stop
      >
        <slot></slot>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 }
})

const emit = defineEmits(['update:modelValue'])

const menuRef = ref(null)
const visible = ref(props.modelValue)
const menuStyle = ref({})

const close = () => {
  emit('update:modelValue', false)
}

const updatePosition = () => {
  if (!visible.value) return

  const menu = menuRef.value
  if (!menu) return

  const rect = menu.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let x = props.x
  let y = props.y

  if (x + rect.width > viewportWidth) {
    x = viewportWidth - rect.width - 8
  }
  if (y + rect.height > viewportHeight) {
    y = viewportHeight - rect.height - 8
  }

  x = Math.max(8, x)
  y = Math.max(8, y)

  menuStyle.value = {
    left: `${x}px`,
    top: `${y}px`
  }
}

watch(() => props.modelValue, async (isOpen) => {
  visible.value = isOpen
  if (isOpen) {
    await nextTick()
    updatePosition()
  }
})

watch([() => props.x, () => props.y], () => {
  if (visible.value) updatePosition()
})

window.addEventListener('resize', updatePosition)
window.addEventListener('scroll', updatePosition)
</script>

<style scoped>
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1500;
}

.context-menu {
  position: fixed;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  padding: 0.25rem;
  min-width: 160px;
  z-index: 1501;
}
</style>
