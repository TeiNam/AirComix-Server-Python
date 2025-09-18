# Comix Server Makefile
# Provides convenient shortcuts for Docker operations

.PHONY: help build build-dev run run-dev stop restart logs status clean test

# Default target
help: ## Show this help message
	@echo "Comix Server Docker Commands"
	@echo "============================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build commands
build: ## Build production Docker image
	@cd docker && docker-compose build

build-dev: ## Build development Docker image
	@cd docker && docker-compose -f docker-compose.dev.yml build

# Run commands
run: ## Start production services
	@cd docker && docker-compose up -d

run-dev: ## Start development services with hot-reload
	@cd docker && docker-compose -f docker-compose.dev.yml up -d

run-fg: ## Start production services in foreground
	@cd docker && docker-compose up

run-build: ## Build and start production services
	@cd docker && docker-compose up -d --build

# Management commands
stop: ## Stop all services
	@cd docker && docker-compose down

stop-dev: ## Stop development services
	@cd docker && docker-compose -f docker-compose.dev.yml down

restart: ## Restart services
	@cd docker && docker-compose restart

logs: ## Show service logs
	@cd docker && docker-compose logs -f

status: ## Show service status
	@cd docker && docker-compose ps

# Maintenance commands
clean: ## Remove stopped containers and unused images
	@echo "Cleaning up Docker resources..."
	@docker container prune -f
	@docker image prune -f
	@echo "Cleanup completed"

clean-all: ## Remove all containers, images, and volumes (DESTRUCTIVE)
	@echo "WARNING: This will remove ALL Docker resources for this project"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker-compose down -v --rmi all
	@docker-compose -f docker-compose.dev.yml down -v --rmi all
	@echo "All resources removed"

# Development commands
test: ## Run tests in Docker container
	@docker-compose -f docker-compose.dev.yml run --rm comix-server-dev python -m pytest

test-cov: ## Run tests with coverage in Docker container
	@docker-compose -f docker-compose.dev.yml run --rm comix-server-dev python -m pytest --cov=app

shell: ## Open shell in running container
	@docker exec -it comix-server /bin/bash

shell-dev: ## Open shell in development container
	@docker exec -it comix-server-dev /bin/bash

# Setup commands
setup: ## Initial setup - copy env file and build
	@echo "Setting up Comix Server..."
	@if [ ! -f docker/.env ]; then \
		cp docker/.env.example docker/.env; \
		echo "Created docker/.env file from template"; \
		echo "Please edit docker/.env file to configure your manga directory"; \
	else \
		echo "docker/.env file already exists"; \
	fi
	@$(MAKE) build
	@echo "Setup completed! Run 'make run' to start the server"

# Quick start
quick-start: setup run ## Complete setup and start (for first-time users)
	@echo ""
	@echo "🚀 Comix Server is starting up!"
	@echo "📁 Don't forget to set MANGA_DIRECTORY in .env file"
	@echo "🌐 Access your server at: http://localhost:31257"
	@echo "📊 Check status with: make status"
	@echo "📋 View logs with: make logs"

# Health check
health: ## Check if service is healthy
	@echo "Checking Comix Server health..."
	@curl -f http://localhost:31257/ > /dev/null 2>&1 && \
		echo "✅ Server is healthy" || \
		echo "❌ Server is not responding"

# Update
update: ## Pull latest changes and rebuild
	@echo "Updating Comix Server..."
	@git pull
	@$(MAKE) build
	@$(MAKE) restart
	@echo "Update completed"