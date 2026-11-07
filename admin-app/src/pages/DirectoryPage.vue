<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ $t('nav.' + kind) }}</h1>
        <p>{{ $t('directory.' + kind) }}</p>
      </div>
      <q-btn
        v-if="editable"
        class="admin-action admin-primary"
        color="primary"
        text-color="dark"
        unelevated
        no-caps
        icon="add"
        :label="$t('common.add')"
        @click="editRecord()"
      />
    </div>

    <q-table
      flat
      wrap-cells
      row-key="id"
      :rows="rows"
      :columns="columns"
      :no-data-label="$t('common.empty')"
      :rows-per-page-options="[10, 25, 50]"
    >
      <template #body-cell-name="props">
        <q-td :props="props">
          <span v-if="props.row.depth" aria-hidden="true">{{ '↳ '.repeat(props.row.depth) }}</span
          >{{ props.value }}
        </q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            no-caps
            class="admin-action"
            :label="$t('common.edit')"
            @click="editRecord(props.row)"
          />
          <q-btn
            v-if="kind === 'categories'"
            flat
            no-caps
            class="admin-action admin-alert"
            :label="$t('common.delete')"
            @click="deleteCategory(props.row)"
          />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialog" persistent>
      <q-card class="admin-dialog">
        <q-card-section>
          <h2 class="admin-section-title">
            {{ $t(draft.id ? 'directory.editRecord' : 'directory.newRecord') }}
          </h2>
        </q-card-section>
        <q-form @submit="save">
          <q-card-section class="q-pt-none q-gutter-y-md">
            <template v-if="kind === 'employees'">
              <q-input
                v-model="draft.first_name"
                outlined
                maxlength="100"
                :label="$t('directory.firstName')"
                :rules="[required]"
              />
              <q-input
                v-model="draft.last_name"
                outlined
                maxlength="100"
                :label="$t('directory.lastName')"
                :rules="[required]"
              />
              <q-input
                v-model="draft.username"
                :readonly="Boolean(draft.id)"
                outlined
                maxlength="50"
                :label="$t('login.username')"
                :rules="[required]"
              />
              <q-select
                v-model="draft.role"
                :options="roleOptions"
                emit-value
                map-options
                outlined
                :label="$t('directory.role')"
              />
              <q-input
                v-model="draft.password"
                outlined
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                maxlength="72"
                :label="$t(draft.id ? 'directory.newPassword' : 'login.password')"
                :hint="$t('directory.passwordHint')"
                :rules="[passwordRule]"
              >
                <template #append>
                  <q-btn
                    flat
                    round
                    dense
                    :icon="showPassword ? 'visibility_off' : 'visibility'"
                    :aria-label="$t(showPassword ? 'login.hidePassword' : 'login.showPassword')"
                    @click="showPassword = !showPassword"
                  />
                  <q-btn
                    flat
                    round
                    dense
                    icon="autorenew"
                    :aria-label="$t('directory.generatePassword')"
                    @click="generatePassword"
                  />
                </template>
              </q-input>
            </template>
            <q-input
              v-else
              v-model="draft.name"
              outlined
              maxlength="150"
              :label="$t('common.name')"
              :rules="[required]"
            />

            <template v-if="kind === 'categories'">
              <q-select
                v-model="draft.parent_id"
                :options="parentOptions"
                option-value="id"
                option-label="name"
                emit-value
                map-options
                outlined
                clearable
                :label="$t('directory.parent')"
              />
              <q-input
                v-model="draft.sort_order"
                outlined
                inputmode="numeric"
                :label="$t('directory.order')"
                :rules="[wholeNumber]"
              />
            </template>
            <template v-if="kind === 'warehouses'">
              <q-input
                v-model="draft.address"
                outlined
                maxlength="255"
                :label="$t('directory.address')"
              />
              <q-toggle v-model="draft.show_on_site" :label="$t('directory.showOnSite')" />
            </template>
            <q-toggle
              v-if="kind !== 'categories'"
              v-model="draft.is_active"
              :label="$t('common.active')"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn
              flat
              no-caps
              class="admin-action"
              :label="$t('common.cancel')"
              @click="dialog = false"
            />
            <q-btn
              class="admin-action"
              type="submit"
              color="primary"
              text-color="dark"
              unelevated
              no-caps
              :label="$t('common.save')"
            />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useInventoryActions } from '../composables/use-inventory-actions.js'
import { employeeName, useInventory } from '../stores/inventory.js'

const props = defineProps({ kind: { type: String, required: true } })
const inventory = useInventory()
const { t } = useI18n()
const { attempt, confirm } = useInventoryActions()
const editable = computed(() => props.kind === 'categories' || inventory.isAdmin)
const dialog = ref(false)
const draft = ref({})
const previousActive = ref(false)
const roleOptions = computed(() =>
  ['admin', 'staff'].map((value) => ({ value, label: t('demo.' + value) })),
)
const parentOptions = computed(() =>
  inventory.categories.filter((item) => item.id !== draft.value.id),
)

function categoryRows(parentId = null, depth = 0) {
  return inventory.categories
    .filter((item) => item.parent_id === parentId)
    .sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name))
    .flatMap((item) => [{ ...item, depth }, ...categoryRows(item.id, depth + 1)])
}
const rows = computed(() => (props.kind === 'categories' ? categoryRows() : inventory[props.kind]))
const columns = computed(() => {
  const name = {
    name: 'name',
    label: t('common.name'),
    field: props.kind === 'employees' ? employeeName : 'name',
    align: 'left',
  }
  const status = {
    name: 'is_active',
    label: t('common.status'),
    field: (row) => t(row.is_active ? 'common.active' : 'common.inactive'),
    align: 'left',
  }
  const actions = { name: 'actions', label: t('common.actions'), field: 'id' }
  if (props.kind === 'categories')
    return [
      name,
      {
        name: 'parent',
        label: t('directory.parent'),
        field: (row) => inventory.categories.find((item) => item.id === row.parent_id)?.name ?? '—',
        align: 'left',
      },
      { name: 'sort_order', label: t('directory.order'), field: 'sort_order' },
      actions,
    ]
  if (props.kind === 'warehouses')
    return [
      name,
      { name: 'address', label: t('directory.address'), field: 'address', align: 'left' },
      {
        name: 'show_on_site',
        label: t('directory.showOnSite'),
        field: (row) => t(row.show_on_site ? 'common.show' : 'common.hidden'),
        align: 'left',
      },
      status,
      ...(editable.value ? [actions] : []),
    ]
  return [
    name,
    { name: 'username', label: t('login.username'), field: 'username', align: 'left' },
    {
      name: 'role',
      label: t('directory.role'),
      field: (row) => t('demo.' + row.role),
      align: 'left',
    },
    status,
    actions,
  ]
})

watch(
  () => props.kind,
  () => {
    dialog.value = false
  },
)
const required = (value) => Boolean(String(value ?? '').trim()) || t('common.required')
const showPassword = ref(false)
// Same policy as the backend: 10+ characters, at least one letter and one digit
function passwordRule(value) {
  const text = String(value ?? '')
  if (!text) return Boolean(draft.value.id) || t('common.required')
  return (
    (text.length >= 10 && /\p{L}/u.test(text) && /\d/.test(text)) || t('directory.passwordHint')
  )
}
function generatePassword() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
  const bytes = crypto.getRandomValues(new Uint32Array(16))
  let value = Array.from(bytes, (n) => alphabet[n % alphabet.length]).join('')
  value = value.slice(0, 14) + 'a7'
  draft.value.password = value
  showPassword.value = true
}
const wholeNumber = (value) => /^\d+$/.test(String(value)) || t('errors.order')

function editRecord(record) {
  const defaults = {
    categories: { name: '', parent_id: null, sort_order: 0 },
    warehouses: { name: '', address: '', show_on_site: false, is_active: true },
    employees: {
      first_name: '',
      last_name: '',
      username: '',
      password: '',
      role: 'staff',
      is_active: true,
    },
  }
  draft.value = { ...(record || defaults[props.kind]), password: '' }
  showPassword.value = false
  previousActive.value = record?.is_active === true
  dialog.value = true
}

function save() {
  const record = { ...draft.value }
  const actions = {
    categories: inventory.saveCategory,
    warehouses: inventory.saveWarehouse,
    employees: inventory.saveEmployee,
  }
  const execute = async () => {
    if (await attempt(() => actions[props.kind](record), 'common.saved')) dialog.value = false
  }
  if (previousActive.value && !record.is_active) {
    confirm(t('directory.deactivate', { name: record.name || employeeName(record) }), execute)
  } else execute()
}

function deleteCategory(record) {
  confirm(t('directory.deleteCategory', { name: record.name }), () => {
    attempt(() => inventory.deleteCategory(record.id), 'common.removed')
  })
}
</script>
