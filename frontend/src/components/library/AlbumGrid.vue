<template>
  <div class="album-grid">
    <AlbumCard
      v-for="album in albums"
      :key="album.id"
      :id="album.id"
      :title="album.title"
      :artist="album.artist"
      :artwork="album.artwork"
      @click="$emit('viewAlbum', album)"
      @play="$emit('playAlbum', album)"
      @contextmenu="$emit('contextmenu', $event, album)"
    />
  </div>
</template>

<script setup>
import AlbumCard from './AlbumCard.vue'

defineProps({
  albums: {
    type: Array,
    required: true
  }
})

defineEmits(['viewAlbum', 'playAlbum', 'contextmenu'])
</script>

<style scoped>
.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 28px;
}

@media (max-width: 1024px) {
  .album-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
}
</style>
