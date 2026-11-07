import { useQuasar } from 'quasar'
import { useI18n } from 'vue-i18n'

export function useDemoActions() {
  const quasar = useQuasar()
  const { t, te } = useI18n()

  function attempt(action, successKey) {
    try {
      const result = action()
      if (successKey)
        quasar.notify({
          message: t(successKey),
          icon: 'check_circle',
          color: 'dark',
          textColor: 'white',
        })
      return result ?? true
    } catch (error) {
      const key = error?.message
      const message = key?.startsWith('errors.') && te(key) ? t(key) : t('errors.generic')
      quasar.notify({ message, icon: 'error', color: 'negative', textColor: 'dark' })
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

  return { attempt, confirm }
}
