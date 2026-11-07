<template>
  <div class="gallery">
    <div v-if="images.length === 0" class="gallery__stage gallery__stage--empty">
      <NoPhoto />
    </div>

    <template v-else>
      <div class="gallery__stage">
        <q-carousel
          v-model="slide"
          animated
          swipeable
          infinite
          :arrows="images.length > 1"
          :navigation="images.length > 1"
          :navigation-icon="mdiCircleSmall"
          :prev-icon="mdiChevronLeft"
          :next-icon="mdiChevronRight"
          control-color="white"
          transition-prev="slide-right"
          transition-next="slide-left"
          class="gallery__carousel"
        >
          <q-carousel-slide v-for="(image, i) in images" :key="image.url" :name="i" class="gallery__slide">
            <button type="button" class="gallery__zoom" :aria-label="t('product.viewPhoto', { n: i + 1, total: images.length })" @click="openZoom(i)">
              <img :src="image.url" :alt="`${name}, ${t('product.photo', { n: i + 1 })}`" :loading="i === 0 ? 'eager' : 'lazy'" />
            </button>
          </q-carousel-slide>
        </q-carousel>
        <span class="gallery__zoom-hint" aria-hidden="true"><q-icon :name="mdiMagnifyPlusOutline" size="20px" /></span>
      </div>

      <ul v-if="images.length > 1" class="gallery__thumbs">
        <li v-for="(image, i) in images" :key="`t-${image.url}`">
          <button
            type="button"
            class="gallery__thumb"
            :class="{ 'is-active': slide === i }"
            :aria-label="t('product.photo', { n: i + 1 })"
            :aria-pressed="slide === i ? 'true' : 'false'"
            @click="slide = i"
          >
            <img :src="image.thumb_url || image.url" alt="" loading="lazy" />
          </button>
        </li>
      </ul>

      <q-dialog v-model="zoomOpen" maximized transition-show="fade" transition-hide="fade">
        <div class="zoom">
          <q-btn flat round class="zoom__close" :icon="mdiClose" :aria-label="t('product.closePhoto')" @click="zoomOpen = false" />
          <q-carousel
            v-model="zoomSlide"
            animated
            swipeable
            infinite
            :arrows="images.length > 1"
            :navigation="images.length > 1"
            :navigation-icon="mdiCircleSmall"
            :prev-icon="mdiChevronLeft"
            :next-icon="mdiChevronRight"
            control-color="white"
            transition-prev="slide-right"
            transition-next="slide-left"
            class="zoom__carousel"
          >
            <q-carousel-slide v-for="(image, i) in images" :key="`z-${image.url}`" :name="i" class="zoom__slide">
              <img :src="image.url" :alt="`${name}, ${t('product.photo', { n: i + 1 })}`" />
            </q-carousel-slide>
          </q-carousel>
        </div>
      </q-dialog>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  mdiChevronLeft,
  mdiChevronRight,
  mdiCircleSmall,
  mdiClose,
  mdiMagnifyPlusOutline,
} from '@quasar/extras/mdi-v7'
import NoPhoto from '../NoPhoto.vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
  name: { type: String, required: true },
})

const { t } = useI18n()

// Main photo first.
const images = computed(() => [...props.images].sort((a, b) => Number(b.is_main) - Number(a.is_main)))

const slide = ref(0)
const zoomOpen = ref(false)
const zoomSlide = ref(0)

watch(
  () => props.images,
  () => {
    slide.value = 0
  },
)

function openZoom(i) {
  zoomSlide.value = i
  zoomOpen.value = true
}
</script>

<style lang="scss" scoped>
.gallery {
  &__stage {
    position: relative;
    aspect-ratio: 4 / 3;
    border-radius: $radius-card;
    overflow: hidden;
    border: 1px solid $color-border;
    background: $color-panel;
  }

  &__carousel {
    height: 100%;
    background: transparent;

    :deep(.q-carousel__navigation-icon--active) {
      color: $primary !important;
    }

    :deep(.q-carousel__navigation-icon) {
      color: rgba(255, 255, 255, 0.6);
    }

    :deep(.q-panel) {
      overflow: hidden;
    }

    :deep(.q-carousel__arrow .q-btn) {
      background: rgba(11, 17, 33, 0.6);
      backdrop-filter: blur(6px);
    }
  }

  &__slide {
    padding: 0;
  }

  &__zoom {
    display: block;
    width: 100%;
    height: 100%;
    padding: 0;
    border: 0;
    background: none;
    cursor: zoom-in;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  &__zoom-hint {
    position: absolute;
    top: 14px;
    right: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: rgba(11, 17, 33, 0.65);
    color: #fff;
    pointer-events: none;
  }

  &__thumbs {
    list-style: none;
    display: flex;
    gap: 10px;
    margin: 12px 0 0;
    padding: 0;
    overflow-x: auto;
  }

  &__thumb {
    display: block;
    width: 92px;
    aspect-ratio: 4 / 3;
    padding: 0;
    border: 2px solid transparent;
    border-radius: 10px;
    overflow: hidden;
    background: $color-panel;
    cursor: pointer;
    opacity: 0.65;
    transition:
      border-color $transition,
      opacity $transition;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    &:hover {
      opacity: 1;
    }

    &.is-active {
      border-color: $primary;
      opacity: 1;
    }
  }
}

.zoom {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: rgba(5, 9, 18, 0.96);

  &__close {
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 2;
    color: #fff;
    background: rgba(255, 255, 255, 0.08);
  }

  &__carousel {
    height: 100%;
    background: transparent;

    :deep(.q-panel) {
      overflow: hidden;
    }

    :deep(.q-carousel__navigation-icon--active) {
      color: $primary !important;
    }
  }

  &__slide {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 64px 16px;

    img {
      max-width: 100%;
      max-height: 100%;
      border-radius: $radius-card;
      object-fit: contain;
    }
  }
}
</style>
