# 📘 RELATÓRIO FINAL DE PLANEJAMENTO & PADRÃO DO PROJETO (MedInteract - Backend)

> **Documento Oficial de Padrão do Projeto**  
> **Status**: Planejamento Concluído e Registrado  
> **Base de Referência**: Diagramas e Fluxos do diretório `Modelo Projeto/`  
> **Arquitetura Selecionada**: Opção 1 — Arquitetura por Camadas (Layered / MVC)  
> **Tecnologias**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, HTTPX, SQLAlchemy 2.0 (Async), PGVector, pdfplumber

---

## 🎯 1. Decisões Tecnológicas e Estrutura de Pastas

### 1.1 Stack Tecnológica do Backend
* **Framework Web**: **FastAPI** (Desempenho assíncrono nativo `async`/`await`, OpenAPI automático em `/docs`).
* **Validação de Dados & DTOs**: **Pydantic v2** (Garantia de schemas fortemente tipados).
* **Servidor ASGI**: **Uvicorn** (Servidor de produção de alta performance).
* **Cliente HTTP Assíncrono**: **HTTPX** (Comunicação não-bloqueante com APIs de IA).
* **Processamento de PDFs & Bulas**: **`pdfplumber`** (Extração de texto de bulas em PDF).
* **Vetorização & RAG**: **Embeddings** + **PGVector** (Busca vetorial por similaridade semântica no banco de dados).
* **ORM / Banco de Dados**: **SQLAlchemy 2.0 (Async)** com PGVector / PostgreSQL (Produção/Docker) e SQLite (Dev local).
* **Task Runner & Atomação**: **`Makefile`** com comandos (`make up`, `make build`, `make dev`, `make restart`, `make down`, `make log`, `make dataBase`, `make seed`, `make test`, `make lint`, `make clean`).

### 1.2 Estrutura Oficial de Arquivos (Arquitetura por Camadas)
```text
backend/
├── main.py                       # Instância principal do FastAPI, Middlewares, CORS e Uvicorn
├── requirements.txt              # Dependências declaradas (FastAPI, PGVector, pdfplumber, etc.)
├── Dockerfile                    # Containerização Uvicorn + Python 3.10
└── app/
    ├── config.py                 # Gerenciamento de envs via Pydantic BaseSettings
    ├── api/                      # Camada de Controladores / Rotas (Controllers)
    │   ├── router.py             # Roteador principal agregador de endpoints (/api)
    │   └── endpoints/            # Módulos de endpoints específicos
    │       ├── chat.py           # Endpoints: POST /api/chat e POST /api/chat/stream
    │       ├── health.py         # Endpoint: GET /api/health
    │       ├── clinical.py       # Endpoints de calculadoras clínicas (Fase 2)
    │       └── drugs.py          # Endpoints de busca de medicamentos e fontes (Fase 3)
    ├── schemas/                  # Camada DTO (Schemas Pydantic)
    │   ├── chat.py               # DTOs do Chat e Streaming
    │   ├── error.py              # DTOs de erros e alertas padronizados da UI
    │   ├── user.py               # DTOs de Usuário (Profissional vs Paciente Comum)
    │   └── clinical.py           # DTOs de cálculo farmacêutico
    ├── services/                 # Camada de Regras de Negócio (Services)
    │   ├── ai_service.py         # Orquestrador assíncrono de IA (Gemini ➔ Claude ➔ Fallback Seguro)
    │   ├── rag_service.py        # Pipeline de busca vetorial no PGVector (`Bula_Chunks`)
    │   ├── prompt_service.py     # System Prompts adaptativos (Profissional vs Paciente + RAG)
    │   ├── pdf_processor.py      # Extração de PDFs com `pdfplumber` e geração de Chunks
    │   └── calculation_service.py# Lógica de cálculos farmacêuticos
    ├── db/                       # Camada de Persistência / Repositories
    │   ├── session.py            # Conexão assíncrona com banco de dados
    │   └── models/               # Entidades SQLAlchemy (`Users`, `Bula_Chunks`, `User_History`, `TrustedSource`)
    └── utils/                    # Utilitários e helpers
        ├── sse.py                # Helper de formatação de eventos SSE (Server-Sent Events)
        └── logger.py             # Logging estruturado da aplicação
```

---

## 🗄️ 2. Modelagem do Banco de Dados (Baseado nos diagramas de `Modelo Projeto/`)

### 2.1 Tabela `Users` (Cadastro de Usuário)
* `id`: UUID / Integer (Chave primária).
* `userName`: String.
* `email`: String (único).
* `passwordhash`: String (hash seguro).
* `profile_type`: `PROFESSIONAL` (Farmacêutico/Médico) ou `PATIENT` (Usuário comum).

### 2.2 Tabela `Bula_Chunks` (Bulas Vetorizadas - PGVector)
* `id_chunck`: UUID / Integer (Chave primária).
* `medName`: String (Nome do medicamento/bula).
* `content`: Text (Trecho do conteúdo extraído pelo `pdfplumber`).
* `embedding`: Vector (Vetor numérico do chunk para busca semântica no PGVector).

### 2.3 Tabela `User_History` (Histórico de Consultas)
* `id_consult`: UUID / Integer (Chave primária).
* `id_user`: FK para `Users.id`.
* `user_question`: Text (Pergunta original do usuário).
* `ia_Answear`: Text (Resposta gerada pela IA/RAG).
* `date_hours`: Timestamp (Data e hora da consulta).

### 2.4 Tabela `TrustedSource` (Fontes Oficiais & Fallback Seguro)
* `id`: Integer.
* `name`: String (ex: *"Bulário Eletrônico da ANVISA"*).
* `url`: String (Link oficial).
* `is_active`: Booleano.

---

## 📌 3. Registro do Estado Atual e Ponto de Parada

> **Data de Registro**: 11/08/2026  
> **Concluído Hoje**:
> 1. ✅ **Planejamento da Arquitetura**: Definição da stack FastAPI + Pydantic + PGVector + pdfplumber.
> 2. ✅ **Fallback Seguro & Prompt Adaptativo**: Regras clínicas de contingência e perfis `PROFESSIONAL` vs `PATIENT`.
> 3. ✅ **Documentação & Memória de Sessão**: Criação dos relatórios em `docs/`, arquivo `GEMINI.md` de contexto automático e `README.md` completo em dupla (Kauã & Sofia).
> 4. ✅ **Segurança Git**: Criação do arquivo [`.gitignore`](file:///C:/workspace/TCC/.gitignore) protegendo chaves de API e arquivos temporários.
> 5. ✅ **Task Runner `Makefile`**: Criação do arquivo [`Makefile`](file:///C:/workspace/TCC/Makefile) com comandos de automação (`make up`, `build`, `dev`, `restart`, `down`, `log`, `dataBase`, `seed`, `test`, `lint`, `clean`).

---

## 📌 4. Próxima Etapa (Onde Paramos)

👉 **Próximo Passo**: Iniciar a **Etapa 1 de Desenvolvimento**:
1. Atualizar o [`docker-compose.yml`](file:///C:/workspace/TCC/docker-compose.yml) para adicionar a imagem do **PostgreSQL + PGVector** (`pgvector/pgvector:pg16`).
2. Atualizar o [`frontend/nginx.conf`](file:///C:/workspace/TCC/frontend/nginx.conf) com as diretivas de streaming SSE (`proxy_buffering off;`).
3. Criar a estrutura física das pastas do FastAPI (`backend/app/api`, `schemas`, `services`, `config.py`, `main.py`).
