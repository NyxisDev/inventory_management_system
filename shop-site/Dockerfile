# syntax=docker/dockerfile:1
# Public catalog (Quasar SSR). Build: docker compose build shop-site

# ---------- build ----------
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
COPY src-ssr/package.json src-ssr/package-lock.json ./src-ssr/
# Scripts are skipped here: "quasar prepare" needs the sources, the build runs it anyway.
RUN npm ci --ignore-scripts --no-audit --no-fund \
 && npm ci --prefix src-ssr --ignore-scripts --no-audit --no-fund

COPY . .
RUN npx quasar build -m ssr

# ---------- runtime ----------
FROM node:24-alpine AS runtime
ENV NODE_ENV=production \
    PORT=3000
WORKDIR /app

COPY --from=build /app/dist/ssr ./
RUN npm install --omit=dev --no-audit --no-fund \
 && npm cache clean --force

# The official image has an unprivileged "node" user.
USER node
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/robots.txt > /dev/null || exit 1

CMD ["node", "index.js"]
