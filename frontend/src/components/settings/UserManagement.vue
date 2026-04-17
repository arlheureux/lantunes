<template>
  <div class="user-management">
    <div class="user-header">
      <h3>Users</h3>
      <button class="btn btn-primary btn-sm" @click="showAddModal = true">
        Add User
      </button>
    </div>

    <div class="user-list">
      <div v-for="u in users" :key="u.id" class="user-row">
        <div class="user-avatar">
          {{ u.username.charAt(0).toUpperCase() }}
        </div>
        <div class="user-info">
          <span class="user-name">{{ u.username }}</span>
          <span class="user-role">{{ u.is_admin ? 'Admin' : 'User' }}</span>
        </div>
        <div class="user-actions">
          <button
            class="icon-btn"
            @click="editUser(u)"
            :disabled="u.id === currentUserId"
          >
            ✎
          </button>
          <button
            class="icon-btn danger"
            @click="deleteUser(u)"
            :disabled="u.id === currentUserId || users.length <= 1"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <Modal v-model="showAddModal" size="small">
      <div class="modal-form">
        <h3>{{ editingUser ? 'Edit User' : 'Add User' }}</h3>
        <div class="form-group">
          <label>Username</label>
          <input
            v-model="form.username"
            type="text"
            class="form-input"
            placeholder="Enter username"
          />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            :placeholder="editingUser ? 'Leave blank to keep current' : 'Enter password'"
          />
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="form.is_admin" type="checkbox" />
            <span>Admin privileges</span>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveUser" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import Modal from '@/components/common/Modal.vue'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import { api } from '@/api'

const { user: currentUser } = useAuth()
const { showToast } = useToast()

const currentUserId = computed(() => currentUser.value?.id)

const users = ref([])
const showAddModal = ref(false)
const editingUser = ref(null)
const saving = ref(false)

const form = reactive({
  username: '',
  password: '',
  is_admin: false
})

const loadUsers = async () => {
  try {
    const response = await api.get('/api/users')
    users.value = response
  } catch (err) {
    showToast('Failed to load users', 'error')
  }
}

const editUser = (u) => {
  editingUser.value = u
  form.username = u.username
  form.password = ''
  form.is_admin = u.is_admin
  showAddModal.value = true
}

const deleteUser = async (u) => {
  if (!confirm(`Delete user "${u.username}"?`)) return

  try {
    await api.delete(`/api/users/${u.id}`)
    showToast('User deleted', 'success')
    loadUsers()
  } catch (err) {
    showToast('Failed to delete user', 'error')
  }
}

const saveUser = async () => {
  if (!form.username.trim()) {
    showToast('Username is required', 'error')
    return
  }

  if (!editingUser.value && !form.password) {
    showToast('Password is required for new users', 'error')
    return
  }

  saving.value = true
  try {
    const payload = {
      username: form.username,
      is_admin: form.is_admin
    }
    if (form.password) {
      payload.password = form.password
    }

    if (editingUser.value) {
      await api.put(`/api/users/${editingUser.value.id}`, payload)
      showToast('User updated', 'success')
    } else {
      await api.post('/api/users', payload)
      showToast('User created', 'success')
    }

    closeModal()
    loadUsers()
  } catch (err) {
    showToast('Failed to save user', 'error')
  } finally {
    saving.value = false
  }
}

const closeModal = () => {
  showAddModal.value = false
  editingUser.value = null
  form.username = ''
  form.password = ''
  form.is_admin = false
}

onMounted(loadUsers)
</script>

<style scoped>
.user-management {
  padding: var(--space-md) 0;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.user-header h3 {
  margin: 0;
  font-size: 1rem;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.user-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.user-actions {
  display: flex;
  gap: var(--space-xs);
}

.icon-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--transition);
}

.icon-btn:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.icon-btn.danger:hover:not(:disabled) {
  color: var(--error);
}

.icon-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.modal-form {
  padding: var(--space-md);
}

.modal-form h3 {
  margin: 0 0 var(--space-lg);
  font-size: 1.25rem;
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.form-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 0.95rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
}

.checkbox-label span {
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
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

.btn-sm {
  padding: var(--space-xs) var(--space-md);
  font-size: 0.8rem;
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
