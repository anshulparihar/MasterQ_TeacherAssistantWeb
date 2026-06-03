.PHONY: up down logs migrate seed shell create-admin

# Start all docker services in detached mode and build them
up:
	docker-compose up -d --build

# Stop and remove all docker services
down:
	docker-compose down

# Tail the logs of all docker services
logs:
	docker-compose logs -f

# Run Alembic migrations to construct the PostgreSQL schema
migrate:
	docker-compose exec backend alembic upgrade head

# Seed initial Subjects and Exam Types data
seed:
	docker-compose exec backend python seed_data.py

# Drop into an interactive shell inside the backend container
shell:
	docker-compose exec backend bash

# Interactive prompt to securely create the first admin user
create-admin:
	docker-compose exec backend python create_admin.py
