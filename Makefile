.DEFAULT_GOAL := help

.PHONY: help install dev test test-unit test-integration test-security \
        lint format type-check docker-build docker-up docker-down \
        terraform-init terraform-plan terraform-validate clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies with uv
	uv sync --all-extras

dev: ## Start API server with hot reload
	uv run uvicorn services.api.src.api.main:app --reload --port 8000 --host 0.0.0.0

test: ## Run all tests
	uv run pytest tests/ -v --tb=short --cov=services --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests (requires running infra)
	uv run pytest tests/integration/ -v --tb=short

test-security: ## Run security/adversarial tests
	uv run pytest tests/security/ -v --tb=short

lint: ## Check code with ruff
	uv run ruff check .
	uv run ruff format --check .

format: ## Format code with ruff
	uv run ruff format .
	uv run ruff check --fix .

type-check: ## Type-check with mypy
	uv run mypy services/ --ignore-missing-imports

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start all services (detached)
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail service logs
	docker compose logs -f

terraform-init: ## Initialize Terraform for dev
	cd infra/envs/azure/dev && terraform init

terraform-plan: ## Plan Terraform for dev
	cd infra/envs/azure/dev && terraform plan

terraform-validate: ## Validate all Terraform modules
	@for d in infra/azure/*/; do \
		echo "Validating $$d..."; \
		cd $$d && terraform init -backend=false -input=false > /dev/null && terraform validate && cd - > /dev/null; \
	done

terraform-fmt: ## Format Terraform files
	terraform fmt -recursive infra/

clean: ## Remove generated artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage 2>/dev/null || true
