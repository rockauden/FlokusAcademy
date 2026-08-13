<script setup>
import { ref } from 'vue'

const props = defineProps({
  initialData: { type: Object, default: () => null }
})
const emit = defineEmits(['submit', 'cancel'])

const form = ref(props.initialData || {
  title: '',
  amount: 0,
  category: 'Curriculum',
  status: 'planned'
})

function submit() {
  emit('submit', form.value)
}
</script>

<template>
  <div class="expense-form">
    <div class="form-group">
      <label>Title</label>
      <input type="text" v-model="form.title" required />
    </div>
    <div class="form-group">
      <label>Amount ($)</label>
      <input type="number" step="0.01" v-model="form.amount" required />
    </div>
    <div class="form-group">
      <label>Category</label>
      <select v-model="form.category">
        <option value="Curriculum">Curriculum</option>
        <option value="Supplies">Supplies</option>
        <option value="Technology">Technology</option>
        <option value="Extracurricular">Extracurricular</option>
      </select>
    </div>
    <div class="form-group">
      <label>Status</label>
      <select v-model="form.status">
        <option value="planned">Planned</option>
        <option value="purchased">Purchased</option>
        <option value="reimbursed">Reimbursed</option>
      </select>
    </div>
    <div class="actions mt-md">
      <button class="btn-primary" @click="submit">Save Expense</button>
      <button class="btn-ghost" @click="$emit('cancel')">Cancel</button>
    </div>
  </div>
</template>

<style scoped>
.expense-form {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.actions { display: flex; gap: var(--space-sm); }
</style>
