.PHONY: help build up down logs restart clean init dev prod

help:
	@echo "McMaster Seat Tracker - Docker Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start all services (development)"
	@echo "  make prod      - Start all services including nginx (production)"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs from all services"
	@echo "  make restart   - Restart all services"
	@echo "  make clean     - Stop and remove all containers, networks, and volumes"
	@echo "  make init      - Initialize database only"
	@echo "  make shell     - Open shell in web container"
	@echo ""

build:
	docker compose build

up:
	docker compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  Web app:  http://localhost:5001"
	@echo "  Admin:    http://localhost:5001/admin/login"
	@echo ""
	@echo "View logs: make logs"

prod:
	docker compose --profile production up -d
	@echo ""
	@echo "✓ Production services started!"
	@echo "  Web app:  http://localhost"
	@echo "  Admin:    http://localhost/admin/login"
	@echo ""

down:
	docker compose --profile production down

logs:
	docker compose logs -f

restart:
	docker compose restart

clean:
	docker compose --profile production down -v
	@echo "✓ All containers, networks, and volumes removed"

init:
	docker compose run --rm init

shell:
	docker compose exec web sh

# Development helpers
dev-logs-web:
	docker compose logs -f web

dev-logs-scraper:
	docker compose logs -f scraper

dev-restart-web:
	docker compose restart web

dev-restart-scraper:
	docker compose restart scraper
