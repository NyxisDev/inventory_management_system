"""HTML sanitizing for product descriptions (bleach).

The frontends clean it again with DOMPurify.
"""

import bleach

ALLOWED_TAGS = frozenset({"p", "br", "b", "strong", "i", "em", "ul", "ol", "li", "h3", "h4", "a"})
ALLOWED_ATTRIBUTES = {"a": ["href"]}
ALLOWED_PROTOCOLS = frozenset({"http", "https", "mailto"})


def clean_description(html: str | None) -> str | None:
    """Keep only the allowed tags; everything else (scripts, styles, handlers) is removed."""
    if html is None:
        return None
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    ).strip()
    return cleaned or None
