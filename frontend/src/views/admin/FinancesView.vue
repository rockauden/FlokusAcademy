<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api/client'
import ExpenseForm from '../../components/admin/ExpenseForm.vue'
import KpiCard from '../../components/common/KpiCard.vue'

const summary = ref(null)
const expenses = ref([])
const showForm = ref(false)

async function fetchData() {
  summary.value = await api.get('/expenses/summary')
  expenses.value = await api.get('/expenses') || []
}

onMounted(fetchData)

async function handleCreate(data) {
  await api.post('/expenses', data)
  showForm.value = false
  await fetchData()
}

async function handleDelete(id) {
  if(confirm('Delete expense?')) {
    await api.delete(`/expenses/${id}`)
    await fetchData()
  }
}
</script>

<template>
  <div class="finances-view">
    <header class="page-header mb-lg">
      <h1>UFA Scholarship Finances</h1>
      <button class="btn-primary" @click="showForm = !showForm">Add Expense</button>
    </header>

    <div v-if="summary" class="kpi-grid mb-lg">
      <KpiCard icon="💰" :value="`$${summary.total_grant}`" label="Total Grant" color="blue" />
      <KpiCard icon="💸" :value="`$${summary.total_spent}`" label="Total Spent" color="orange" />
      <KpiCard icon="🏦" :value="`$${summary.remaining}`" label="Remaining" :color="summary.remaining < 600 ? 'red' : 'green'" />
    </div>

    <div v-if="showForm" class="mb-lg">
      <ExpenseForm @submit="handleCreate" @cancel="showForm = false" />
    </div>

    <div class="table-panel">
      <h3>Expense Ledger</h3>
      <table class="data-table mt-md">
        <thead>
          <tr>
            <th>Date</th>
            <th>Title</th>
            <th>Category</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ex in expenses" :key="ex.id">
            <td>{{ new Date(ex.date_logged).toLocaleDateString() }}</td>
            <td>{{ ex.title }}</td>
            <td>{{ ex.category }}</td>
            <td>${{ ex.amount }}</td>
            <td>
              <span class="badge" :class="{'badge-green': ex.status==='reimbursed', 'badge-orange': ex.status==='planned'}">
                {{ ex.status }}
              </span>
            </td>
            <td>
              <button class="btn-ghost" @click="handleDelete(ex.id)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
}
.table-panel {
  background: var(--bg-card);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th, .data-table td {
  padding: var(--space-sm);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}
</style>
