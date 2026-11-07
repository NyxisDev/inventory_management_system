import { randomBytes } from 'node:crypto'
import { defineSsrMiddleware } from '#q-app'

// Content Security Policy for the catalog pages. Inline scripts (the serialized
// state that Quasar adds) are allowed only with the per-request nonce.
function contentSecurityPolicy(nonce) {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}'`,
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join('; ')
}

/**
 * Renders every remaining GET request with Vue. Must be the last middleware.
 * Pages can set ssrContext.httpStatus (for example 404 for an unknown product).
 */
export default defineSsrMiddleware(({ app, resolve, render, serve }) => {
  app.get(resolve.urlPath('/*'), async (c) => {
    const req = c.env.incoming
    const res = c.env.outgoing
    const nonce = randomBytes(16).toString('base64')
    const ssrContext = { req, res, nonce, httpStatus: 200 }

    try {
      const renderedHtml = await render(ssrContext)
      const headers = {
        // Stock changes with every warehouse operation: always revalidate pages.
        'Cache-Control': 'no-cache',
      }
      // Vite's dev server injects its own inline scripts, so CSP is production only.
      if (import.meta.env.QUASAR_PROD) headers['Content-Security-Policy'] = contentSecurityPolicy(nonce)
      return c.html(renderedHtml, ssrContext.httpStatus, headers)
    } catch (err) {
      if (err?.routeNotFound) {
        return c.html('404 | Page Not Found', 404)
      }

      if (err?.redirectUrl) {
        return c.redirect(err.redirectUrl, err.redirectHttpStatusCode)
      }

      if (import.meta.env.QUASAR_DEV) {
        const { errorHtml, errorHeaders } = serve.devError({ err, req })
        return c.html(errorHtml, 500, errorHeaders)
      }

      // Details go to the server log only, never to the visitor.
      console.error(err instanceof Error ? err.stack : (err ?? 'Unknown error'))
      return c.html(
        '<!doctype html><title>Server error</title><body style="background:#0b1121;color:#fff;font-family:system-ui;padding:48px"><h1>Something went wrong</h1><p>Please try again in a moment.</p></body>',
        500,
      )
    }
  })
})
