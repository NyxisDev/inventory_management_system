import { defineBoot } from '#q-app'

// v-reveal: blocks fade up when they scroll into view (catalog site only).
// The server renders content fully visible. On the client, only elements that
// are still below the fold are hidden and then revealed, so nothing flashes
// and nothing stays hidden without JavaScript or with reduced motion.

let observer = null

function getObserver() {
  if (observer === null) {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const el = entry.target
            el.classList.add('reveal-done')
            el.classList.remove('reveal-pending')
            observer.unobserve(el)
          }
        }
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
    )
  }
  return observer
}

const reveal = {
  getSSRProps() {
    return {}
  },
  mounted(el, binding) {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const rect = el.getBoundingClientRect()
    if (rect.top < window.innerHeight * 0.92) return

    const delay = Number(binding.value) || 0
    if (delay > 0) el.style.transitionDelay = `${delay}ms`
    el.classList.add('reveal-pending')
    getObserver().observe(el)
  },
  beforeUnmount(el) {
    if (observer !== null) observer.unobserve(el)
  },
}

export default defineBoot(({ app }) => {
  app.directive('reveal', reveal)
})
