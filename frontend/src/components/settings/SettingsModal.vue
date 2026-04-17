<template>
  <Modal :model-value="modelValue" size="medium" :show-close="true" @close="close" @update:model-value="$emit('update:modelValue', $event)">
    <div class="settings-modal">
      <div class="settings-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="settings-content">
        <div v-if="activeTab === 'general'" class="settings-section">
          <h3>Library</h3>
          <div class="setting-row">
            <div class="setting-info">
              <label>Music Path</label>
              <p class="setting-desc">Where your music files are stored</p>
            </div>
            <input type="text" v-model="settings.music_path" class="setting-input" />
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <label>Auto-scan on startup</label>
              <p class="setting-desc">Automatically scan for new music when the app starts</p>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="settings.auto_scan" />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <h3>Playback</h3>
          <div class="setting-row">
            <div class="setting-info">
              <label>Crossfade</label>
              <p class="setting-desc">Duration of crossfade between tracks (seconds)</p>
            </div>
            <input type="number" v-model="settings.crossfade" min="0" max="12" class="setting-input setting-number" />
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <label>Gapless playback</label>
              <p class="setting-desc">Remove silence between tracks</p>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="settings.gapless" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div v-else-if="activeTab === 'appearance'" class="settings-section">
          <h3>Theme</h3>
          <div class="theme-options">
            <button
              v-for="theme in themes"
              :key="theme.id"
              class="theme-btn"
              :class="{ active: settings.theme === theme.id }"
              @click="settings.theme = theme.id"
            >
              <div class="theme-preview" :style="{ background: theme.bg, color: theme.fg }">
                <span>Aa</span>
              </div>
              <span>{{ theme.label }}</span>
            </button>
          </div>

          <h3>Display</h3>
          <div class="setting-row">
            <div class="setting-info">
              <label>Album grid columns</label>
              <p class="setting-desc">Number of columns in the album grid</p>
            </div>
            <select v-model="settings.album_columns" class="setting-input">
              <option value="auto">Auto</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
              <option value="6">6</option>
            </select>
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <label>Show track numbers</label>
              <p class="setting-desc">Display track numbers in album views</p>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="settings.show_track_numbers" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div v-else-if="activeTab === 'audio'" class="settings-section">
          <h3>Output</h3>
          <div class="setting-row">
            <div class="setting-info">
              <label>Audio Device</label>
              <p class="setting-desc">Device to use for audio output</p>
            </div>
            <select v-model="settings.audio_device" class="setting-input">
              <option value="default">Default</option>
              <option value="hdmi">HDMI</option>
              <option value="analog">Analog</option>
            </select>
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <label>Volume normalization</label>
              <p class="setting-desc">Normalize volume across all tracks</p>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="settings.volume_normalization" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="setting-row">
            <div class="setting-info">
              <label>ReplayGain</label>
              <p class="setting-desc">Apply ReplayGain tags if available</p>
            </div>
            <select v-model="settings.replaygain" class="setting-input">
              <option value="off">Off</option>
              <option value="track">Track</option>
              <option value="album">Album</option>
            </select>
          </div>

          <h3>Advanced</h3>
          <div class="setting-row">
            <div class="setting-info">
              <label>Audio buffer size</label>
              <p class="setting-desc">Higher values reduce stuttering but increase memory</p>
            </div>
            <select v-model="settings.buffer_size" class="setting-input">
              <option value="1024">Low (1024)</option>
              <option value="2048">Medium (2048)</option>
              <option value="4096">High (4096)</option>
            </select>
          </div>
        </div>

        <div v-else-if="activeTab === 'users'" class="settings-section">
          <UserManagement v-if="isAdmin" />
          <div v-else class="no-permission">
            <p>You need admin privileges to manage users.</p>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button class="btn btn-primary" @click="saveSettings" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
  </Modal>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import Modal from '@/components/common/Modal.vue'
import UserManagement from './UserManagement.vue'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { api } from '@/api'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'close'])

const { user } = useAuth()
const { showToast } = useToast()

const isAdmin = computed(() => user.value?.is_admin)
const activeTab = ref('general')
const saving = ref(false)

const tabs = [
  { id: 'general', label: 'General' },
  { id: 'appearance', label: 'Appearance' },
  { id: 'audio', label: 'Audio' },
  { id: 'users', label: 'Users' }
]

const themes = [
  { id: 'dark', label: 'Dark', bg: '#1a1a2e', fg: '#eaeaea' },
  { id: 'light', label: 'Light', bg: '#f5f5f5', fg: '#1a1a2e' },
  { id: 'system', label: 'System', bg: 'linear-gradient(135deg, #1a1a2e 50%, #f5f5f5 50%)', fg: '#eaeaea' }
]

const settings = reactive({
  music_path: '/home/arnaud/Music',
  auto_scan: true,
  crossfade: 0,
  gapless: false,
  theme: 'dark',
  album_columns: 'auto',
  show_track_numbers: true,
  audio_device: 'default',
  volume_normalization: false,
  replaygain: 'off',
  buffer_size: '2048'
})

const loadSettings = async () => {
  try {
    const config = await api.get('/api/config')
    Object.assign(settings, config)
  } catch (err) {
    console.error('Failed to load settings:', err)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await api.post('/api/config', settings)
    showToast('Settings saved successfully', 'success')
    close()
  } catch (err) {
    showToast('Failed to save settings', 'error')
  } finally {
    saving.value = false
  }
}

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

if (props.modelValue) loadSettings()
</script>

<style scoped>
.settings-modal {
  min-height: 400px;
}

.settings-tabs {
  display: flex;
  gap: var(--space-xs);
  border-bottom: 1px solid var(--bg-tertiary);
  padding-bottom: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.tab-btn {
  padding: var(--space-sm) var(--space-md);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition);
}

.tab-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--primary);
  color: white;
}

.settings-content {
  min-height: 300px;
}

.settings-section h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin: 0 0 var(--space-md);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--bg-tertiary);
}

.setting-info label {
  display: block;
  font-size: 0.95rem;
  color: var(--text-primary);
  margin-bottom: 0.125rem;
}

.setting-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
}

.setting-input {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 0.9rem;
  min-width: 180px;
}

.setting-input:focus {
  outline: none;
  border-color: var(--primary);
}

.setting-number {
  width: 80px;
  text-align: center;
}

.toggle {
  position: relative;
  width: 48px;
  height: 26px;
  cursor: pointer;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--bg-tertiary);
  border-radius: 13px;
  transition: background var(--transition);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition);
}

.toggle input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.theme-options {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.theme-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm);
  background: none;
  border: 2px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
}

.theme-btn.active {
  border-color: var(--primary);
}

.theme-preview {
  width: 60px;
  height: 40px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.theme-btn span:last-child {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.no-permission {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
}

.settings-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--bg-tertiary);
  margin-top: var(--space-lg);
}

.btn {
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-secondary {
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.btn-primary {
  background: var(--primary);
  border: none;
  color: white;
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
