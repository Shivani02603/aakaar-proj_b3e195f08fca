.PHONY: install dev build test docker-up docker-down clean

install:
	@echo "Installing dependencies..."
	@pip install -r backend/requirements.txt
	@npm install --prefix frontend

dev:
	@echo "Starting development environment..."
	@./scripts/dev.sh

build:
	@echo "Building frontend..."
	@npm run build --prefix frontend

test:
	@echo "Running tests..."
	@pytest backend/tests
	@npm test --prefix frontend

docker-up:
	@echo "Starting Docker containers..."
	@docker-compose up --build -d

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

clean:
	@echo "Cleaning up..."
	@rm -rf backend/__pycache__ frontend/node_modules frontend/dist
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type f -name "*.pyc" -delete