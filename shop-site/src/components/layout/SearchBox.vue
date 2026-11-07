<template>
  <form class="search-box" role="search" :class="{ 'search-box--large': large }" @submit.prevent="submit">
    <label :for="inputId" class="visually-hidden">{{ t('search.label') }}</label>
    <div class="search-box__field">
      <q-icon :name="mdiMagnify" class="search-box__icon" aria-hidden="true" />
      <input
        :id="inputId"
        ref="inputRef"
        v-model="query"
        type="search"
        class="search-box__input"
        :placeholder="t('search.placeholder')"
        autocomplete="off"
        maxlength="100"
        role="combobox"
        aria-autocomplete="list"
        :aria-expanded="open ? 'true' : 'false'"
        :aria-controls="listId"
        :aria-activedescendant="activeIndex >= 0 ? optionId(activeIndex) : undefined"
        @input="onInput"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.esc="close"
        @focus="onFocus"
        @blur="onBlur"
      />
      <q-spinner v-if="loading" size="18px" color="primary" class="search-box__spinner" />
      <button type="submit" class="search-box__submit" :aria-label="t('search.submit')">
        <q-icon :name="mdiArrowRight" />
      </button>
    </div>

    <div v-show="open" :id="listId" class="search-box__panel" role="listbox" :aria-label="t('search.label')">
      <template v-if="suggestions.length">
        <router-link
          v-for="(item, i) in suggestions"
          :id="optionId(i)"
          :key="item.slug"
          :to="{ name: 'product', params: { slug: item.slug } }"
          class="search-box__item"
          :class="{ 'is-active': i === activeIndex }"
          role="option"
          :aria-selected="i === activeIndex ? 'true' : 'false'"
          tabindex="-1"
          @mousedown.prevent
          @click="close"
        >
          <span class="search-box__thumb">
            <img v-if="thumb(item)" :src="thumb(item)" alt="" loading="lazy" />
            <NoPhoto v-else compact />
          </span>
          <span class="search-box__text">
            <span class="search-box__name">{{ item.name }}</span>
            <span class="search-box__meta">{{ item.sku }}</span>
          </span>
          <span class="search-box__price">{{ formatPrice(item.price) }}</span>
        </router-link>
        <router-link
          :to="{ name: 'search', query: { q: query.trim() } }"
          class="search-box__all"
          tabindex="-1"
          @mousedown.prevent
          @click="close"
        >
          {{ t('search.seeAll', { q: query.trim() }) }}
          <q-icon :name="mdiArrowRight" size="18px" />
        </router-link>
      </template>
      <p v-else class="search-box__empty">{{ t('search.noSuggestions', { q: query.trim() }) }}</p>
    </div>
  </form>
</template>

<script setup>
import { onBeforeUnmount, ref, useId, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { mdiArrowRight, mdiMagnify } from '@quasar/extras/mdi-v7'
import { useCatalogStore } from '@/stores/catalog'
import { useFormat } from '@/composables/use-format'
import NoPhoto from '../NoPhoto.vue'

const props = defineProps({
  large: { type: Boolean, default: false },
  initial: { type: String, default: '' },
})
const emit = defineEmits(['done'])

const MIN_CHARS = 2
const DEBOUNCE_MS = 300

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const catalog = useCatalogStore()
const { formatPrice } = useFormat()

const uid = useId()
const inputId = 'search-' + uid
const listId = 'search-list-' + uid
const inputRef = ref(null)
const query = ref(props.initial)
const suggestions = ref([])
const open = ref(false)
const loading = ref(false)
const activeIndex = ref(-1)
let timer = null
let requestNo = 0

watch(
  () => props.initial,
  (value) => {
    query.value = value
  },
)

// Close the panel when the user navigates away.
watch(
  () => route.fullPath,
  () => close(),
)

function optionId(i) {
  return listId + '-' + i
}

function thumb(item) {
  return item.main_image?.thumb_url || item.main_image?.url || ''
}

function onInput() {
  clearTimeout(timer)
  activeIndex.value = -1
  const q = query.value.trim()
  if (q.length < MIN_CHARS) {
    suggestions.value = []
    open.value = false
    loading.value = false
    return
  }
  loading.value = true
  timer = setTimeout(() => fetchSuggestions(q), DEBOUNCE_MS)
}

async function fetchSuggestions(q) {
  const no = ++requestNo
  try {
    const { items } = await catalog.suggest(q)
    if (no !== requestNo) return
    suggestions.value = items
    open.value = true
  } catch {
    if (no === requestNo) {
      suggestions.value = []
      open.value = false
    }
  } finally {
    if (no === requestNo) loading.value = false
  }
}

function move(step) {
  if (!open.value || suggestions.value.length === 0) return
  const count = suggestions.value.length
  activeIndex.value = (activeIndex.value + step + count) % count
}

function onFocus() {
  if (suggestions.value.length && query.value.trim().length >= MIN_CHARS) open.value = true
}

function onBlur() {
  // Let a click on a suggestion finish first.
  setTimeout(() => {
    open.value = false
  }, 150)
}

function close() {
  open.value = false
  activeIndex.value = -1
}

function submit() {
  const q = query.value.trim()
  const active = suggestions.value[activeIndex.value]
  if (open.value && active) {
    router.push({ name: 'product', params: { slug: active.slug } })
  } else if (q) {
    router.push({ name: 'search', query: { q } })
  }
  close()
  inputRef.value?.blur()
  emit('done')
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })

onBeforeUnmount(() => clearTimeout(timer))
</script>

<style lang="scss" scoped>
.search-box {
  position: relative;
  width: 100%;

  &__field {
    display: flex;
    align-items: center;
    height: 48px;
    padding: 0 6px 0 14px;
    border: 1px solid $color-border-strong;
    border-radius: $radius-button;
    background: rgba(255, 255, 255, 0.04);
    transition:
      border-color $transition,
      background-color $transition;

    &:focus-within {
      border-color: $primary;
      background: rgba(255, 255, 255, 0.06);
    }
  }

  &--large &__field {
    height: 60px;
    padding-left: 18px;
  }

  &__icon {
    color: $color-text-muted;
    font-size: 20px;
    flex: none;
  }

  &__input {
    flex: 1;
    min-width: 0;
    height: 100%;
    padding: 0 10px;
    border: 0;
    outline: none;
    background: transparent;
    color: $color-text;
    font: inherit;
    font-size: 1rem;

    &::placeholder {
      color: $color-text-muted;
    }

    &::-webkit-search-cancel-button {
      filter: invert(0.7);
    }
  }

  &__spinner {
    margin-right: 6px;
  }

  &__submit {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: 0;
    border-radius: 6px;
    background: $primary;
    color: #fff;
    font-size: 20px;
    cursor: pointer;
    transition: background-color $transition;

    &:hover {
      background: $color-primary-hover;
    }
  }

  &--large &__submit {
    width: 46px;
    height: 46px;
  }

  &__panel {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    z-index: 2100;
    padding: 6px;
    border: 1px solid $color-border;
    border-radius: 12px;
    background: $color-panel;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px;
    border-radius: 8px;
    color: $color-text;

    &:hover,
    &.is-active {
      background: rgba(255, 255, 255, 0.06);
      color: $color-text;
    }
  }

  &__thumb {
    position: relative;
    flex: none;
    width: 48px;
    height: 36px;
    border-radius: 6px;
    overflow: hidden;
    background: $color-panel-raised;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  &__text {
    display: flex;
    flex-direction: column;
    min-width: 0;
    flex: 1;
  }

  &__name {
    font-size: 0.9375rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__meta {
    font-size: 0.75rem;
    color: $color-text-muted;
  }

  &__price {
    flex: none;
    font-family: $font-heading;
    font-weight: 700;
    color: $primary;
  }

  &__all {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 4px;
    padding: 10px 8px;
    border-top: 1px solid $color-border;
    font-size: 0.875rem;
    font-weight: 600;
    color: $primary;

    &:hover {
      color: $color-primary-hover;
    }
  }

  &__empty {
    padding: 14px 10px;
    font-size: 0.875rem;
    color: $color-text-muted;
  }
}
</style>
