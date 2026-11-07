<template>
  <div class="card product-skeleton" aria-hidden="true">
    <q-skeleton class="product-skeleton__img" square />
    <div class="product-skeleton__body">
      <q-skeleton type="text" width="40%" />
      <q-skeleton type="text" width="90%" />
      <q-skeleton type="text" width="70%" />
      <q-skeleton type="text" width="50%" class="q-mt-md" height="28px" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.product-skeleton {
  overflow: hidden;

  &__img {
    margin: 8px 8px 0;
    border-radius: 12px;
    aspect-ratio: 4 / 3;
    height: auto;
  }

  &__body {
    padding: 16px 18px 18px;
  }
}
</style>
