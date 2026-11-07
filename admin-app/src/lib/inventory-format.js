const priceFormat = new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' })
const quantityFormat = new Intl.NumberFormat('en-IE', { maximumFractionDigits: 3 })

export const units = ['pcs', 'kg', 'm', 'm²', 'm³', 'l', 'pack']
export const stockOperations = ['income', 'outcome', 'transfer', 'adjustment']
export const movementTypes = ['income', 'outcome', 'transfer_out', 'transfer_in', 'adjustment']

function parseDecimal(input, integerDigits, fractionDigits) {
  const value = String(input ?? '')
    .trim()
    .replace(',', '.')
  const [integer, fraction = ''] = value.split('.')
  if (
    !/^\d+(?:\.\d+)?$/.test(value) ||
    integer.length > integerDigits ||
    fraction.length > fractionDigits
  ) {
    return null
  }

  return BigInt(integer + fraction.padEnd(fractionDigits, '0'))
}

export function parseQuantity(input) {
  return parseDecimal(input, 11, 3)
}

export function parsePrice(input) {
  return parseDecimal(input, 10, 2)
}

export function decimalString(value, fractionDigits = 3) {
  const sign = value < 0n ? '-' : ''
  const digits = String(value < 0n ? -value : value).padStart(fractionDigits + 1, '0')
  return sign + digits.slice(0, -fractionDigits) + '.' + digits.slice(-fractionDigits)
}

export function formatPrice(value) {
  return priceFormat.format(value)
}

export function formatQuantity(value, unit) {
  const formatted = quantityFormat.format(value)
  return unit ? formatted + ' ' + unit : formatted
}

function datePart(value) {
  return String(value).padStart(2, '0')
}

export function dateKey(date) {
  return [date.getFullYear(), datePart(date.getMonth() + 1), datePart(date.getDate())].join('-')
}

export function formatDate(value) {
  const date = new Date(value)
  const day = [datePart(date.getDate()), datePart(date.getMonth() + 1), date.getFullYear()].join(
    '.',
  )
  return day + ' ' + datePart(date.getHours()) + ':' + datePart(date.getMinutes())
}

export function compareDecimal(left, right) {
  const leftValue = BigInt(left.replace('.', ''))
  const rightValue = BigInt(right.replace('.', ''))
  if (leftValue === rightValue) return 0
  return leftValue > rightValue ? 1 : -1
}

export function queryValue(value) {
  return typeof value === 'string' ? value : ''
}
