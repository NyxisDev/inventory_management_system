# Shortcuts for Docker Compose. Run "make help" for the list.
COMPOSE       = docker compose
COMPOSE_HTTPS = docker compose -f docker-compose.yml -f docker-compose.https.yml
COMPOSE_DEMO  = docker compose -f docker-compose.demo.yml

.PHONY: help up down build logs ps migrate seed test check security-check backup restore https demo demo-down

help:
	@echo "up              start everything (http://localhost:8080 and :8081)"
	@echo "down            stop everything (data stays in the volumes)"
	@echo "build           rebuild the images"
	@echo "logs            follow the logs"
	@echo "migrate         apply database migrations"
	@echo "seed            create the first admin (ADMIN_USERNAME / ADMIN_PASSWORD from .env)"
	@echo "test            backend tests"
	@echo "check           linters (ruff, ty, eslint)"
	@echo "security-check  linters + pip-audit + npm audit"
	@echo "backup          database dump + photos into backups/"
	@echo "restore         make restore DB=backups/db_x.dump MEDIA=backups/media_x.tar.gz"
	@echo "https           production start with HTTPS (Caddy)"
	@echo "demo            catalog only, on demo data (http://localhost:8080)"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) exec backend alembic upgrade head

seed:
	$(COMPOSE) exec backend python -m app.seed

test:
	$(COMPOSE) exec backend python -m pytest

check:
	bash scripts/check.sh

security-check:
	bash scripts/check.sh --security

backup:
	bash scripts/backup.sh

restore:
	bash scripts/restore.sh $(DB) $(MEDIA)

https:
	$(COMPOSE_HTTPS) up -d --build

demo:
	$(COMPOSE_DEMO) up -d --build

demo-down:
	$(COMPOSE_DEMO) down
