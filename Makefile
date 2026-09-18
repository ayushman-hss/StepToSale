.PHONY: db-up db-down migrate backend frontend sample

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

sample:
	cd backend && python scripts/generate_sample.py