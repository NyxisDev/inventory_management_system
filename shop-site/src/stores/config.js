import { defineStore } from 'pinia'

// Public shop settings. Filled on the server from .env (boot/config.js)
// and hydrated in the browser from the serialized state.
export const useConfigStore = defineStore('config', {
  state: () => ({
    siteName: '',
    siteUrl: '',
    phone: '',
    email: '',
    address: '',
    hours: [],
    currency: 'EUR',
    mock: false,
    // Interface language chosen for this request (see i18n/locales.js).
    locale: 'en',
  }),
  getters: {
    phoneHref: (state) => `tel:${state.phone.replace(/[^\d+]/g, '')}`,
    emailHref: (state) => `mailto:${state.email}`,
  },
})
