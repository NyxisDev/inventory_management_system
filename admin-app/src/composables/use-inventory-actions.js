// Runs a (possibly async) store action, shows a success or error notification.
// Errors: "errors.<key>" is translated; "api:<text>" is the backend's English message.
import { useQuasar } from 'quasar'
import { useI18n } from 'vue-i18n'

export function useInventoryActions() {
  const quasar = useQuasar()
  const { t, te } = useI18n()

  function errorMessage(error) {
    const key = error?.message ?? ''
    if (key.startsWith('api:')) return key.slice(4)
    return key.startsWith('errors.') && te(key) ? t(key) : t('errors.generic')
  }

  async function attempt(action, successKey) {
    try {
      const result = await action()
      if (successKey)
        quasar.notify({
          message: t(successKey),
          icon: 'check_circle',
          color: 'dark',
          textColor: 'white',
        })
      return result ?? true
    } catch (error) {
      quasar.notify({
        message: errorMessage(error),
        icon: 'error',
        color: 'negative',
        textColor: 'white',
      })
      return null
    }
  }

  function confirm(message, action) {
    quasar
      .dialog({
        title: t('common.confirmTitle'),
        message,
        cancel: { label: t('common.cancel'), flat: true, noCaps: true },
        ok: { label: t('common.confirm'), color: 'primary', textColor: 'dark', noCaps: true },
        persistent: true,
      })
      .onOk(action)
  }

  return { attempt, confirm, errorMessage }
}
