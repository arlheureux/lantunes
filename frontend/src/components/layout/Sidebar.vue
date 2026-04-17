<template>
  <div class="sidebar">
    <div class="sidebar-logo">
      <i class="fas fa-music"></i> LanTunes
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'library' }"
      @click="$emit('navigate', 'library')"
    >
      <i class="fas fa-home"></i> Home
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'tracks' }"
      @click="$emit('navigate', 'tracks')"
    >
      <i class="fas fa-list"></i> All Tracks
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'albums' }"
      @click="$emit('navigate', 'albums')"
    >
      <i class="fas fa-compact-disc"></i> Albums
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'artists' }"
      @click="$emit('navigate', 'artists')"
    >
      <i class="fas fa-user"></i> Artists
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'genres' }"
      @click="$emit('navigate', 'genres')"
    >
      <i class="fas fa-music"></i> Genres
    </div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'playlists' }"
      @click="$emit('navigate', 'playlists')"
    >
      <i class="fas fa-heart"></i> Playlists
    </div>
    
    <div class="sidebar-section">Settings</div>
    
    <div
      class="sidebar-item"
      :class="{ active: view === 'settings' }"
      @click="$emit('navigate', 'settings')"
    >
      <i class="fas fa-cog"></i> Settings
    </div>
    
    <div class="sidebar-item" @click="$emit('logout')" style="color: #ff6b6b;">
      <i class="fas fa-sign-out-alt"></i> Logout
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

defineEmits(['navigate', 'logout'])
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%);
  padding: 20px 0;
  border-right: 1px solid var(--border-subtle);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  padding: 0 24px 24px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: -0.5px;
}

.sidebar-logo i {
  color: var(--accent);
  filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.4));
}

.sidebar-item {
  padding: 14px 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  border-left: 3px solid transparent;
  font-weight: 500;
  font-size: 14px;
}

.sidebar-item:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.sidebar-item.active {
  color: var(--accent);
  background: var(--accent-muted);
  border-left-color: var(--accent);
}

.sidebar-item i {
  width: 20px;
  font-size: 16px;
}

.sidebar-section {
  padding: 24px 24px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
}
</style>
