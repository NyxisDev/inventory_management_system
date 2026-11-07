# syntax=docker/dockerfile:1
# Employee app (Quasar SPA). Build context is ./admin-app (see docker-compose.yml).
# Expects a Quasar project with package-lock.json; output in dist/spa.

# ---------- build ----------
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY . .
RUN npx quasar build

# ---------- runtime: static files, runs as a non-root user ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /app/dist/spa /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    server_tokens off;

    # Hashed build files never change: cache them for a year.
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }

    # SPA fallback: unknown paths are handled by Vue Router.
    location / {
        add_header Cache-Control "no-cache";
        try_files $uri $uri/ /index.html;
    }
}
EOF
EXPOSE 8080
