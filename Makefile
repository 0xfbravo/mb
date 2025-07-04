# Variables
PYTHON=python3
PIP=pip3
PYTEST=pytest
COVERAGE=coverage
BLACK=black
FLAKE8=flake8
MYPY=mypy
ISORT=isort
DOCKER_REGISTRY=gcr.io
PROJECT_ID=mb

# Include .env file if it exists
-include .env

# Export all variables from .env
export

# Colors for terminal output
CYAN=\033[0;36m
GREEN=\033[0;32m
RED=\033[0;31m
NC=\033[0m # No Color

# Default target
.PHONY: all
all: clean build test/unit

# Development tools setup
.PHONY: setup
setup: setup-venv setup-lefthook setup-lint setup-formatter

.PHONY: setup-venv
setup-venv:
	@echo "${CYAN}🔍 Setting up Python virtual environment...${NC}"
	@if [ ! -d "venv" ]; then \
		$(PYTHON) -m venv venv; \
		echo "${GREEN}✅ Virtual environment created${NC}"; \
	else \
		echo "${GREEN}✅ Virtual environment already exists${NC}"; \
	fi
	@echo "${CYAN}📦 Installing dependencies...${NC}"
	@. venv/bin/activate && $(PIP) install -r requirements.txt --quiet
	@. venv/bin/activate && $(PIP) install -r requirements-dev.txt --quiet

.PHONY: setup-lefthook
setup-lefthook:
	@echo "${CYAN}🔍 Installing lefthook via pip...${NC}"
	@. venv/bin/activate && $(PIP) install lefthook --quiet
	@echo "${GREEN}✅ lefthook installed${NC}"
	@echo "${CYAN}🔧 Installing lefthook hooks...${NC}"
	@. venv/bin/activate && lefthook install

.PHONY: setup-lint
setup-lint:
	@echo "${CYAN}🔍 Installing linting tools...${NC}"
	@. venv/bin/activate && $(PIP) install flake8 mypy --quiet

.PHONY: setup-formatter
setup-formatter:
	@echo "${CYAN}🔍 Installing formatting tools...${NC}"
	@. venv/bin/activate && $(PIP) install black isort --quiet

# Docker permission check
.PHONY: check-docker
check-docker:
	@echo "${CYAN}🔍 Checking Docker permissions...${NC}"
	@if ! groups | grep -q docker; then \
		echo "${RED}❌ Your user is not in the docker group. Please run:${NC}"; \
		echo "sudo usermod -aG docker $$USER"; \
		echo "Then log out and log back in, or run: newgrp docker"; \
		exit 1; \
	fi
	@if ! docker info > /dev/null 2>&1; then \
		echo "${RED}❌ Cannot connect to Docker daemon. Please ensure Docker is running and you have proper permissions.${NC}"; \
		exit 1; \
	fi
	@echo "${GREEN}✅ Docker permissions verified${NC}"

# Build targets
.PHONY: clean build
build: check-docker
	@echo "${CYAN}🐳 Building Docker image...${NC}"
	@if [ ! -f .env ]; then \
		echo "${RED}❌ .env file not found. Please create one with required environment variables.${NC}"; \
		exit 1; \
	fi
	@echo "${CYAN}🔑 Building monolith application...${NC}"
	@docker build \
		--build-arg ENV=$(ENV) \
		--build-arg VERSION=$(VERSION) \
		--build-arg PORT=$(PORT) \
		-t $(DOCKER_REGISTRY)/$(PROJECT_ID)/mb:$(VERSION) .

# Docker Compose targets
.PHONY: up
up: check-docker
	@echo "${CYAN}🐳 Starting services with Docker Compose...${NC}"
	@if [ ! -f .env ]; then \
		echo "${RED}❌ .env file not found. Please create one with required environment variables.${NC}"; \
		exit 1; \
	fi
	@docker compose up -d

.PHONY: up/build
up/build: check-docker
	@echo "${CYAN}🐳 Building and starting services with Docker Compose...${NC}"
	@if [ ! -f .env ]; then \
		echo "${RED}❌ .env file not found. Please create one with required environment variables.${NC}"; \
		exit 1; \
	fi
	@docker compose up -d --build

.PHONY: down
down:
	@echo "${CYAN}🐳 Stopping services with Docker Compose...${NC}"
	@docker compose down

.PHONY: down/volumes
down/volumes:
	@echo "${CYAN}🐳 Stopping services and removing volumes with Docker Compose...${NC}"
	@docker compose down -v

.PHONY: logs
logs:
	@echo "${CYAN}📋 Showing Docker Compose logs...${NC}"
	@docker compose logs -f

.PHONY: logs/web
logs/web:
	@echo "${CYAN}📋 Showing web service logs...${NC}"
	@docker compose logs -f api

.PHONY: logs/postgres
logs/postgres:
	@echo "${CYAN}📋 Showing postgres service logs...${NC}"
	@docker compose logs -f postgres

.PHONY: install
install:
	@echo "${CYAN}📦 Installing package...${NC}"
	@. venv/bin/activate && $(PIP) install -e . --quiet

# Clean target
.PHONY: clean
clean:
	@echo "${CYAN}🧹 Cleaning up...${NC}"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .mypy_cache/
	@find . -type d -name __pycache__ -not -path "./venv/*" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -not -path "./venv/*" -not -path "./.venv/*" -delete

# Test targets
.PHONY: test
test: clean setup check-docker test/unit test/integration coverage

.PHONY: test/unit
test/unit:
	@echo "${CYAN}🐢 Running unit tests...${NC}"
	@. venv/bin/activate && $(PYTEST) test/unit/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-report=json

.PHONY: test/integration
test/integration: check-docker
	@echo "${CYAN}🏎️ Running integration tests...${NC}"
	@. venv/bin/activate && $(PYTEST) test/integration/ -v

.PHONY: test/all
test/all:
	@echo "${CYAN}🧪 Running all tests...${NC}"
	@. venv/bin/activate && $(PYTEST) test/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-report=json

.PHONY: coverage
coverage:
	@echo "${CYAN}📊 Generating coverage report...${NC}"
	@. venv/bin/activate && $(COVERAGE) report
	@. venv/bin/activate && $(COVERAGE) html

# Mock generation (using pytest-mock)
.PHONY: mocks
mocks:
	@echo "${CYAN}🎭 Mocks are handled by pytest-mock during testing...${NC}"

# Linting and formatting
.PHONY: lint
lint: setup-lint fmt
	@echo "${CYAN}🔍 Running linter...${NC}"
	@. venv/bin/activate && $(FLAKE8) app/ main.py
	@. venv/bin/activate && $(MYPY) app/ main.py

.PHONY: lint/fix
lint/fix: setup-lint
	@echo "${CYAN}🔍 Running linter with auto-fix...${NC}"
	@. venv/bin/activate && $(FLAKE8) . --count --select=E9,F63,F7,F82 --show-source --statistics

.PHONY: fmt
fmt: setup-formatter
	@echo "${CYAN}🎨 Formatting code...${NC}"
	@. venv/bin/activate && $(BLACK) .
	@. venv/bin/activate && $(ISORT) .

.PHONY: code-pattern
code-pattern: fmt lint/fix

# Dependencies
.PHONY: deps
deps:
	@echo "${CYAN}📦 Installing dependencies...${NC}"
	@. venv/bin/activate && $(PIP) install -r requirements.txt --quiet

.PHONY: deps/update
deps/update:
	@echo "${CYAN}📦 Updating dependencies...${NC}"
	@. venv/bin/activate && $(PIP) install --upgrade -r requirements.txt --quiet
	@. venv/bin/activate && $(PIP) install --upgrade -r requirements-dev.txt --quiet

.PHONY: deps/compile
deps/compile:
	@echo "${CYAN}📦 Compiling requirements...${NC}"
	@. venv/bin/activate && $(PIP) install pip-tools --quiet
	@. venv/bin/activate && pip-compile requirements.in --strip-extras
	@. venv/bin/activate && pip-compile requirements-dev.in --strip-extras

# Security checks
.PHONY: security
security:
	@echo "${CYAN}🔒 Running security checks...${NC}"
	@. venv/bin/activate && $(PIP) install safety --quiet
	@. venv/bin/activate && safety scan

# Development server
.PHONY: run
run:
	@echo "${CYAN}🚀 Starting development server...${NC}"
	@. venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: run/dev
run/dev:
	@echo "${CYAN}🚀 Starting development server with auto-reload...${NC}"
	@. venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Help target
.PHONY: help
help:
	@echo "${CYAN}Available targets:${NC}"
	@echo "${GREEN}all${NC}               - Clean, build and test the application"
	@echo "${GREEN}build${NC}             - Build Docker image for the monolith"
	@echo "${GREEN}install${NC}           - Install the package in development mode"
	@echo "${GREEN}clean${NC}             - Clean build artifacts"
	@echo "${GREEN}coverage${NC}          - Generate test coverage report"
	@echo "${GREEN}deps${NC}              - Install dependencies"
	@echo "${GREEN}deps/update${NC}       - Update dependencies"
	@echo "${GREEN}deps/compile${NC}      - Compile requirements files"
	@echo "${GREEN}fmt${NC}               - Format code with black and isort"
	@echo "${GREEN}lint${NC}              - Run linter (flake8 and mypy)"
	@echo "${GREEN}mocks${NC}             - Mock generation info"
	@echo "${GREEN}run${NC}               - Run the application"
	@echo "${GREEN}run/dev${NC}           - Run with auto-reload"
	@echo "${GREEN}security${NC}          - Run security checks"
	@echo "${GREEN}setup${NC}             - Setup development environment (includes lefthook)"
	@echo "${GREEN}test${NC}              - Run all tests"
	@echo "${GREEN}test/unit${NC}         - Run unit tests"
	@echo "${GREEN}test/integration${NC}  - Run integration tests"
	@echo "${GREEN}test/all${NC}          - Run all tests with coverage"
	@echo ""
	@echo "${CYAN}Docker Compose targets:${NC}"
	@echo "${GREEN}up${NC}                - Start services with Docker Compose"
	@echo "${GREEN}up/build${NC}          - Build and start services with Docker Compose"
	@echo "${GREEN}down${NC}              - Stop services with Docker Compose"
	@echo "${GREEN}down/volumes${NC}      - Stop services and remove volumes"
	@echo "${GREEN}logs${NC}              - Show all service logs"
	@echo "${GREEN}logs/web${NC}          - Show web service logs"
	@echo "${GREEN}logs/postgres${NC}     - Show postgres service logs"