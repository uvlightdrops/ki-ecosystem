.PHONY: init install update test lint deploy clean help prod-update

help:
	@echo "KI Ecosystem stackctl commands"
	@echo ""
	@echo "Development:"
	@echo "  make init          Initialize all sibling repositories"
	@echo "  make install       Install all dependencies"
	@echo "  make update        Update all sibling repositories"
	@echo ""
	@echo "Quality:"
	@echo "  make test          Run tests across all projects"
	@echo "  make lint          Lint all projects"
	@echo "  make audit         Audit dependencies for vulnerabilities"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy        Deploy using stack configuration"
	@echo "  make prod-update   Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Clean build artifacts and caches"

# Initialize all sibling repositories
init:
	@echo "Initializing all sibling repositories..."
	stackctl init

# Install dependencies
install:
	@echo "Installing ki-ecosystem and all siblings..."
	pip install -e ".[dev]"

# Update all siblings
update:
	@echo "Updating all sibling repositories..."
	stackctl update

# Run tests
test:
	@echo "Running tests across all projects..."
	stackctl run pytest

# Lint code
lint:
	@echo "Linting all projects..."
	stackctl run "ruff check ."

# Audit dependencies
audit:
	@echo "Auditing dependencies for vulnerabilities..."
	stackctl run "pip-audit"

# Deploy stack
deploy:
	@echo "Deploying stack configuration..."
	stackctl deploy

# Production deployment
prod-update:
	@echo "Production update:"
	@echo "  1. Running tests..."
	$(MAKE) test
	@echo "  2. Linting..."
	$(MAKE) lint
	@echo "  3. Deploying..."
	$(MAKE) deploy
	@echo "✅ Production deployment complete"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts and caches..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"
