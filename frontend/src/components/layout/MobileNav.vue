<template>
  <div class="mobile-nav">
    <div
      class="mobile-nav-item"
      :class="{ active: view === 'library' }"
      @click="$emit('navigate', 'library')"
    >
      <i class="fas fa-home"></i>
      Home
    </div>
    
    <div
      class="mobile-nav-item"
      :class="{ active: view === 'tracks' }"
      @click="$emit('navigate', 'tracks')"
    >
      <i class="fas fa-music"></i>
      Tracks
    </div>
    
    <div
      class="mobile-nav-item"
      @click="$emit('showMore')"
    >
      <i class="fas fa-bars"></i>
      More
    </div>
    
    <div
      class="mobile-nav-item"
      :class="{ active: view === 'artists' }"
      @click="$emit('navigate', 'artists')"
    >
      <i class="fas fa-user"></i>
      Artists
    </div>
    
    <div
      class="mobile-nav-item"
      :class="{ active: view === 'settings' }"
      @click="$emit('navigate', 'settings')"
    >
      <i class="fas fa-cog"></i>
      Settings
    </div>
  </div>
</template>

<script setup>
defineProps({
  view: {
    type: String,
    default: 'library'
  }
})

defineEmits(['navigate', 'showMore'])
</script>

<style scoped>
.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px 4px;
  min-width: 0;
  border-radius: 0;
  transition: all 0.2s ease;
  position: relative;
  min-height: 56px;
}

.mobile-nav-item:active {
  background: var(--bg-hover);
}

.mobile-nav-item.active {
  color: var(--accent);
}

.mobile-nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 15%;
  right: 15%;
  height: 3px;
  background: var(--accent);
  border-radius: 3px 3px 0 0;
}

.mobile-nav-item i {
  font-size: 24px;
  margin-bottom: 6px;
}
</style>
