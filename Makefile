# ==========================================
#         Comandos de Inicialização
# ==========================================

.PHONY: up down build dev restart log

up:
	docker-compose up -d

down: 
	docker-compose down

build: 
	docker-compose up --build -d

dev: 
	docker-compose up

restart: 
	docker-compose restart

log: 	
	docker-compose logs -f

# ==========================================
#       Comandos de banco e execuções
# ==========================================

.PHONY: dataBase migrations seed test lint clean 

dataBase: 
	docker-compose exec postgres-db psql -U postgres -d medinteract

seed: 
	docker-compose exec ai-engine python -m app.db.seed

test: 
	docker-compose exec ai-engine pytest

lint: 
	docker-compose exec ai-engine flake8 app

clean: 
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"