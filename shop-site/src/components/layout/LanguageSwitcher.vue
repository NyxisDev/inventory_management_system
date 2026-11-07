<template>
  <!-- Compact menu for the header -->
  <q-btn
    v-if="variant === 'menu'"
    flat
    no-caps
    class="lang-btn"
    :aria-label="`${t('nav.language')}: ${current.name}`"
  >
    <q-icon :name="mdiTranslate" size="18px" class="lang-btn__icon" aria-hidden="true" />
    <span class="lang-btn__code">{{ current.short }}</span>
    <q-icon :name="mdiChevronDown" size="16px" class="lang-btn__chevron" aria-hidden="true" />

    <q-menu anchor="bottom right" self="top right" :offset="[0, 8]" class="lang-menu">
      <q-list role="menu" :aria-label="t('nav.language')">
        <q-item
          v-for="l in locales"
          :key="l.code"
          v-close-popup
          clickable
          role="menuitemradio"
          :aria-checked="l.code === current.code ? 'true' : 'false'"
          :lang="l.tag"
          class="lang-menu__item"
          :class="{ 'is-active': l.code === current.code }"
          @click="setLocale(l.code)"
        >
          <q-item-section side class="lang-menu__code">{{ l.short }}</q-item-section>
          <q-item-section>{{ l.name }}</q-item-section>
          <q-item-section v-if="l.code === current.code" side>
            <q-icon :name="mdiCheck" size="18px" color="primary" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>

  <!-- Segmented buttons for the mobile menu -->
  <div v-else class="lang-seg" role="group" :aria-label="t('nav.language')">
    <button
      v-for="l in locales"
      :key="l.code"
      type="button"
      class="lang-seg__btn"
      :class="{ 'is-active': l.code === current.code }"
      :aria-pressed="l.code === current.code ? 'true' : 'false'"
      :lang="l.tag"
      @click="setLocale(l.code)"
    >
      {{ l.name }}
    </button>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { mdiCheck, mdiChevronDown, mdiTranslate } from '@quasar/extras/mdi-v7'
import { useLocale } from '@/composables/use-locale'

defineProps({
  variant: { type: String, default: 'menu', validator: (v) => ['menu', 'segmented'].includes(v) },
})

const { t } = useI18n()
const { locales, current, setLocale } = useLocale()
</script>

<style lang="scss" scoped>
.lang-btn {
  min-height: 44px;
  padding: 0 10px;
  border-radius: $radius-button;
  color: $color-text;
  font-weight: 600;
  font-size: 0.9375rem;

  :deep(.q-btn__content) {
    gap: 6px;
    flex-wrap: nowrap;
  }

  &__icon,
  &__chevron {
    color: $color-text-muted;
  }

  &:hover &__icon {
    color: $primary;
  }
}

.lang-seg {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 4px;
  padding: 4px;
  border: 1px solid $color-border;
  border-radius: $radius-button;
  background: $color-page;

  &__btn {
    min-height: 44px;
    padding: 0 12px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: $color-text-muted;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    transition:
      background-color $transition,
      color $transition;

    &:hover {
      color: $color-text;
    }

    &.is-active {
      background: $color-primary-soft;
      color: $primary;
    }
  }
}
</style>

<style lang="scss">
// The menu is teleported to <body>, so these styles cannot be scoped.
.lang-menu {
  min-width: 200px;

  .lang-menu__item {
    min-height: 44px;
    color: $color-text;

    &.is-active {
      color: $primary;
    }
  }

  .lang-menu__code {
    min-width: 32px;
    padding-right: 8px;
    font-size: 0.8125rem;
    font-weight: 600;
    color: $color-text-muted;
  }
}
</style>
