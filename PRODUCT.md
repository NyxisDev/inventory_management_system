# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vue 3 + Quasar 2 (Vite, Pinia). `admin-app` is a client-side app for employees. `shop-site` is a server-side rendered public catalog. API: FastAPI on PostgreSQL.

## Users

- **Customers** of a building-materials shop (no account). They compare products, check price and exact stock in each warehouse, and then phone or visit the shop. They often use a phone.
- **Staff** record income, outcome, transfers and stock-taking during the working day, often repeatedly and on a tablet or phone in the warehouse.
- **Admins** also manage employees and review the audit log.

## Product Purpose

One place for multi-warehouse stock records and a public catalog that always shows true stock. Success: staff can record an operation in a few taps without mistakes, and a customer sees accurate price and availability without calling.

## Positioning

The catalog shows exact live stock per warehouse, and the same data drives the employee app. Every change is traceable in an append-only audit log.

## Operating Context

No online ordering and no cart: the catalog leads to a phone call or a visit. Shop contacts, address and opening hours come from `.env`. Units include pcs, kg, m, m², m³, l and pack, so quantities can be fractional.

## Capabilities and Constraints

- Roles: `admin` and `staff`. Customers are read-only.
- The catalog site is in English and Slovak (switcher in the header; choice kept in a `lang` cookie, `?lang=sk` links for search engines). Ukrainian is planned. Product and category names come from the data and are not translated.
- Currency comes from the `CURRENCY` setting (default EUR).
- Open decisions: shop name, logo, real contacts, photography.

## Brand Commitments

Dark theme with an orange accent, in the style of https://budmaster.netlify.app/ (style only, no copied text, images or logo). Colours, fonts and component rules are in `AGENTS.md` (Design) and `docs/agent-rules.md`.

## Evidence on Hand

None yet. There is no logo, real product photography, product data or shop copy. Use placeholders and clearly marked sample text. Do not invent claims, testimonials, certifications, prices or contact details.

## Product Principles

- Accuracy over decoration: stock and price are the most important information on every screen.
- Scanning over reading: tables, badges and filters must be readable at a glance, especially in the admin app.
- Mobile first: both apps are used on phones and tablets.
- Calm admin, confident catalog: the employee app stays quiet for long sessions, the public site carries the brand.

## Accessibility & Inclusion

WCAG AA contrast, visible keyboard focus, `prefers-reduced-motion` respected, touch targets at least 44 px.
