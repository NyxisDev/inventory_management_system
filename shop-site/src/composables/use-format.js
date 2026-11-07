import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfigStore } from '@/stores/config'

// Prices and quantities arrive as decimal strings ("120.00", "12.500").
// They are only formatted for display here, never used for arithmetic.

const formatters = new Map()

function cached(key, make) {
  if (!formatters.has(key)) formatters.set(key, make())
  return formatters.get(key)
}

export function useFormat() {
  const config = useConfigStore()
  const { t, te, locale } = useI18n()

  const priceFormatter = computed(() =>
    cached(
      `price:${locale.value}:${config.currency}`,
      () =>
        new Intl.NumberFormat(locale.value, {
          style: 'currency',
          currency: config.currency,
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
    ),
  )

  const qtyFormatter = computed(() =>
    cached(`qty:${locale.value}`, () => new Intl.NumberFormat(locale.value, { maximumFractionDigits: 3 })),
  )

  function unitLabel(unit) {
    return te(`units.${unit}`) ? t(`units.${unit}`) : unit
  }

  function formatPrice(value) {
    const n = Number(value)
    return Number.isFinite(n) ? priceFormatter.value.format(n) : ''
  }

  function formatQty(value, unit) {
    const n = Number(value)
    const text = Number.isFinite(n) ? qtyFormatter.value.format(n) : '0'
    return unit ? `${text} ${unitLabel(unit)}` : text
  }

  function isInStock(value) {
    return Number(value) > 0
  }

  return { formatPrice, formatQty, unitLabel, isInStock }
}
