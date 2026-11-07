import DOMPurify from 'isomorphic-dompurify'

// Product descriptions come from the admin editor. The backend already cleans
// them with bleach; this is the second layer before v-html (server and browser).
const OPTIONS = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'ul', 'ol', 'li', 'h2', 'h3', 'h4', 'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
  ALLOWED_ATTR: ['href', 'title'],
  ALLOW_DATA_ATTR: false,
  ALLOWED_URI_REGEXP: /^(?:https?:|mailto:|tel:|\/(?!\/))/i,
}

let hookAdded = false

export function sanitizeHtml(html) {
  if (!html) return ''
  if (!hookAdded) {
    // Links in descriptions open safely in a new tab.
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.tagName === 'A') {
        node.setAttribute('target', '_blank')
        node.setAttribute('rel', 'noopener noreferrer nofollow')
      }
    })
    hookAdded = true
  }
  return DOMPurify.sanitize(String(html), OPTIONS)
}
