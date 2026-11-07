<template>
  <q-page class="admin-page">
    <div class="admin-heading">
      <div>
        <h1>{{ product?.name || $t(isNew ? 'products.add' : 'products.edit') }}</h1>
        <p v-if="product">{{ product.sku }}</p>
      </div>
      <q-btn
        flat
        no-caps
        class="admin-action"
        icon="arrow_back"
        :label="$t('common.back')"
        :to="{ name: 'app-products' }"
      />
    </div>

    <p v-if="!isNew && !product" class="admin-panel q-pa-md">{{ $t('errors.productMissing') }}</p>
    <template v-else>
      <q-banner v-if="product?.is_archived" class="admin-panel q-mb-md">{{
        $t('products.archivedNote')
      }}</q-banner>
      <q-tabs
        v-if="product"
        :model-value="activeTab"
        align="left"
        no-caps
        class="q-mb-md"
        @update:model-value="setTab"
      >
        <q-tab name="details" :label="$t('products.details')" />
        <q-tab name="photos" :label="$t('products.photos')" />
        <q-tab name="stock" :label="$t('products.stock')" />
        <q-tab name="history" :label="$t('products.history')" />
      </q-tabs>

      <q-form
        v-if="activeTab === 'details'"
        class="admin-panel admin-form-grid q-pa-md"
        @submit="save"
      >
        <q-input
          v-model="draft.name"
          :readonly="product?.is_archived"
          outlined
          :label="$t('common.name')"
          maxlength="255"
          :rules="[required]"
        />
        <q-input
          v-model="draft.sku"
          :readonly="product?.is_archived"
          outlined
          :label="$t('common.sku')"
          maxlength="64"
          :rules="[required]"
        />
        <q-select
          v-model="draft.category_id"
          :readonly="product?.is_archived"
          :options="inventory.categories"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          clearable
          outlined
          :label="$t('common.category')"
        />
        <q-select
          v-model="draft.unit"
          :readonly="product?.is_archived || hasStockHistory"
          :options="units"
          outlined
          :label="$t('common.unit')"
          :rules="[required]"
        />
        <q-input
          v-model="draft.price"
          :readonly="product?.is_archived"
          outlined
          inputmode="decimal"
          :label="$t('common.price') + ' (€)'"
          :rules="[validPrice]"
        />
        <q-toggle
          v-model="draft.is_published"
          :disable="product?.is_archived"
          :label="$t('common.published')"
        />
        <q-input
          v-model="draft.description"
          :readonly="product?.is_archived"
          outlined
          type="textarea"
          class="admin-form-wide"
          :label="$t('common.description')"
          maxlength="2000"
        />
        <div v-if="!product?.is_archived" class="admin-form-wide">
          <q-btn
            class="admin-action admin-primary"
            type="submit"
            color="primary"
            text-color="dark"
            unelevated
            no-caps
            :label="$t('common.save')"
          />
        </div>
      </q-form>

      <div v-if="activeTab === 'photos'" class="admin-panel q-pa-md">
        <q-file
          v-if="!product.is_archived"
          v-model="uploads"
          multiple
          outlined
          accept="image/jpeg,image/png,image/webp"
          max-file-size="5242880"
          :label="$t('products.uploadPhotos')"
          :hint="$t('products.uploadHint')"
          :loading="uploading"
          @update:model-value="uploadPhotos"
          @rejected="onRejected"
        >
          <template #prepend><q-icon name="add_photo_alternate" /></template>
        </q-file>
        <p v-if="!images.length" class="admin-muted q-mt-md q-mb-none">
          {{ $t('products.noPhotos') }}
        </p>
        <div class="photo-grid q-mt-md">
          <div v-for="image in images" :key="image.id" class="photo-card">
            <q-img :src="image.thumb_url" :ratio="1" class="photo-img" />
            <div class="photo-actions">
              <q-badge v-if="image.is_main" color="primary" text-color="dark">
                {{ $t('products.mainPhoto') }}
              </q-badge>
              <q-btn
                v-else-if="!product.is_archived"
                flat
                dense
                no-caps
                icon="star"
                :label="$t('products.makeMain')"
                @click="makeMain(image.id)"
              />
              <q-btn
                v-if="!product.is_archived"
                flat
                dense
                round
                icon="delete"
                :aria-label="$t('products.deletePhoto')"
                @click="removePhoto(image.id)"
              />
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'stock'" class="admin-panel q-pa-md">
        <q-list separator>
          <q-item
            v-for="warehouse in inventory.warehouses"
            :key="warehouse.id"
            class="stock-row q-px-none q-py-md"
          >
            <q-item-section>
              <q-item-label>{{ warehouse.name }}</q-item-label>
              <q-item-label caption>{{
                formatQuantity(
                  inventory.stockAt(product.id, warehouse.id)?.quantity ?? '0',
                  product.unit,
                )
              }}</q-item-label>
            </q-item-section>
            <q-item-section side v-if="!product.is_archived && warehouse.is_active">
              <q-form class="minimum-form" @submit="saveMinimum(warehouse.id)">
                <q-input
                  v-model="minimums[warehouse.id]"
                  outlined
                  inputmode="decimal"
                  :label="$t('products.minimum')"
                  :aria-label="$t('products.minimumFor', { name: warehouse.name })"
                  :rules="[validQuantity]"
                  hide-bottom-space
                />
                <q-btn flat no-caps class="admin-action" type="submit" :label="$t('common.save')" />
              </q-form>
            </q-item-section>
          </q-item>
        </q-list>
        <q-btn
          v-if="!product.is_archived"
          class="admin-action q-mt-md"
          color="primary"
          text-color="dark"
          unelevated
          no-caps
          :label="$t('products.openStock')"
          :to="{ name: 'app-stock', query: { product: String(product.id) } }"
        />
      </div>

      <template v-if="activeTab === 'history'">
        <MovementTable :rows="history" />
        <div v-if="inventory.isAdmin" class="admin-panel q-pa-md q-mt-md">
          <h2 class="text-subtitle1 q-mt-none q-mb-sm">{{ $t('products.changeHistory') }}</h2>
          <p v-if="!changeLog.length" class="admin-muted q-mb-none">{{ $t('audit.empty') }}</p>
          <q-list v-else separator dense>
            <q-item v-for="entry in changeLog" :key="entry.id">
              <q-item-section>
                <q-item-label>{{ entry.label }}</q-item-label>
                <q-item-label caption>{{ formatDate(entry.created_at) }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>
      </template>
    </template>
  </q-page>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '../boot/axios.js'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import MovementTable from '../components/MovementTable.vue'
import { useInventoryActions } from '../composables/use-inventory-actions.js'
import {
  formatDate,
  formatQuantity,
  parsePrice,
  parseQuantity,
  units,
} from '../lib/inventory-format.js'
import { useInventory } from '../stores/inventory.js'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const inventory = useInventory()
const { attempt, confirm } = useInventoryActions()
const quasar = useQuasar()
const tabs = ['details', 'photos', 'stock', 'history']
const isNew = computed(() => route.name === 'app-product-new')
const product = computed(() =>
  isNew.value ? undefined : inventory.products.find((item) => item.id === Number(route.params.id)),
)
const activeTab = computed(() =>
  product.value && tabs.includes(route.query.tab) ? route.query.tab : 'details',
)
const history = ref([])
const changeLog = ref([])
const images = ref([])
const uploads = ref(null)
const uploading = ref(false)
const hasStockHistory = computed(
  () =>
    history.value.length > 0 || inventory.stock.some((row) => row.product_id === product.value?.id),
)

// Description, photos and history come from the product's own endpoints
async function loadDetails(id) {
  if (!id) return
  const [details, movements, audit] = await Promise.all([
    inventory.loadProductDetails(id),
    api.get('/stock/movements', { params: { product_id: id, page_size: 100 } }),
    inventory.productHistory(id),
  ])
  images.value = details.images
  history.value = movements.data.items
  changeLog.value = audit
  draft.description = details.description ?? ''
  snapshot.value = JSON.stringify(draft)
}
watch(
  () => product.value?.id,
  (id) => attempt(() => loadDetails(id)),
)
onMounted(() => attempt(() => loadDetails(product.value?.id)))

async function uploadPhotos(files) {
  if (!files?.length) return
  uploading.value = true
  const details = await attempt(
    () => inventory.uploadImages(product.value.id, files),
    'common.saved',
  )
  uploading.value = false
  uploads.value = null
  if (details) images.value = details.images
}
async function makeMain(imageId) {
  const details = await attempt(() => inventory.setMainImage(product.value.id, imageId))
  if (details) images.value = details.images
}
function removePhoto(imageId) {
  confirm(t('products.deletePhotoConfirm'), async () => {
    const details = await attempt(
      () => inventory.deleteImage(product.value.id, imageId),
      'common.removed',
    )
    if (details) images.value = details.images
  })
}
function onRejected() {
  quasar.notify({ message: t('products.uploadHint'), color: 'negative', icon: 'error' })
}
const draft = reactive({})
const minimums = reactive({})
const snapshot = ref('')

watch(
  product,
  (value) => {
    Object.assign(
      draft,
      value || {
        id: null,
        sku: '',
        name: '',
        price: '',
        unit: 'pcs',
        category_id: null,
        is_published: false,
        description: '',
      },
    )
    for (const warehouse of inventory.warehouses)
      minimums[warehouse.id] = inventory.stockAt(value?.id, warehouse.id)?.min_quantity ?? '0'
    snapshot.value = JSON.stringify(draft)
  },
  { immediate: true },
)

const required = (value) => Boolean(String(value ?? '').trim()) || t('common.required')
const validPrice = (value) => parsePrice(value) !== null || t('errors.price')
const validQuantity = (value) => parseQuantity(value) !== null || t('errors.quantity')
const allowLeave = () =>
  JSON.stringify(draft) === snapshot.value || window.confirm(t('products.leave'))

onBeforeRouteLeave(allowLeave)
onBeforeRouteUpdate(
  (to, from) => (to.name === from.name && to.params.id === from.params.id) || allowLeave(),
)

function setTab(tab) {
  router.replace({ query: { ...route.query, tab } })
}

async function save() {
  const id = await attempt(() => inventory.saveProduct(draft), 'common.saved')
  if (id === null) return
  snapshot.value = JSON.stringify(draft)
  router.replace({ name: 'app-product', params: { id } })
}

function saveMinimum(warehouseId) {
  attempt(
    () => inventory.setMinimum(product.value.id, warehouseId, minimums[warehouseId]),
    'common.saved',
  )
}
</script>

<style scoped>
.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.photo-card {
  border: 1px solid var(--admin-border, rgba(255, 255, 255, 0.1));
  border-radius: 12px;
  overflow: hidden;
}

.photo-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 6px 8px;
  min-height: 44px;
}

.minimum-form {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 599px) {
  .stock-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .stock-row :deep(.q-item__section--side) {
    padding: 0;
  }
}
</style>
