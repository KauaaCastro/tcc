# ⚕️ MedInteract — Plataforma de Análise de Interações Medicamentosas com IA & RAG

> **Trabalho de Conclusão de Curso (TCC)**  
> **Autores**: Kauã Ricardo de Castro Galvão & Sofia David de Carvalho  
> **Instituição**: Plataforma Web de Suporte à Decisão Farmacológica Clínica

---

## 📌 1. Sobre o Projeto

O **MedInteract** é uma plataforma web inteligente desenvolvida para realizar análises de interações medicamentosas, fornecendo suporte à decisão clínica para profissionais de saúde (farmacêuticos, médicos e enfermeiros) e orientações didáticas e seguras para pacientes e usuários comuns.

A plataforma combina modelos de linguagem de última geração (**Google Gemini**) com a técnica de **RAG (Retrieval-Augmented Generation)** e o **Prompt Sanduíche**, realizando buscas por similaridade semântica em bulas oficiais da ANVISA armazenadas em um banco de dados vetorial (**PostgreSQL + PGVector**) e cruzando com a ficha clínica do paciente (`farm_history`).

### 🎯 Principais Diferenciais
* **Perfil Adaptativo (`PROFESSIONAL` vs `PATIENT`)**: Respostas em linguagem técnica farmacológica para profissionais ou linguagem acolhedora e acessível para pacientes.
* **Prompt Sanduíche & Ficha Clínica (`farm_history`)**: Ancoragem estrita nas bulas da ANVISA (`<bula>`), cruzamento seguro com dados do paciente (`<perfil_paciente>`: idade, IMC calculado, gestação/lactação, alergias, medicações contínuas, esportes e sono) e sanitização contra *Prompt Injection*.
* **Streaming em Tempo Real (SSE)**: Transmissão da análise palavra por palavra via Server-Sent Events (`/api/chat/stream`), reduzindo o tempo de espera percebido.
* **Calculadoras Farmacêuticas Determinísticas (`farmCalc`)**: Cálculo matemático estrito em Java para Dose Pediátrica por Peso e Clearance de Creatinina (Cockcroft-Gault), sem risco de alucinação.
* **Fallback Seguro de Saúde**: Caso a IA esteja indisponível, o sistema **não gera simulações médicas arbitrárias**; aciona o alerta `restriction` e exibe links oficiais pré-aprovados (ANVISA e Medscape).
* **Guardrails de Escopo**: Bloqueio automático de perguntas fora do contexto médico/farmacológico.

---

## 🛠️ 2. Arquitetura e Tecnologias Utilizadas

### **🐍 Backend IA & RAG (`backend/ai-engine` — Porta `5000`)**
* **Linguagem & Framework**: Python 3.10+ com **FastAPI** (Assíncrono, Swagger em `/docs`)
* **Validação & DTOs**: **Pydantic v2**
* **Servidor ASGI**: **Uvicorn**
* **ORM & Banco Vetorial**: **SQLAlchemy 2.0 (Async)** + **PGVector** (índice HNSW para busca de similaridade de cosseno em vetores de 768 dimensões)
* **Extração de Bulas**: **`pdfplumber`** (Processamento e chunking de PDFs oficiais da ANVISA)
* **Provedor de IA**: Google Gemini API (`gemini-3.5-flash-lite` / `gemini-3.5-flash` + `gemini-embedding-001`) via **HTTPX**

### **☕ Backend Core API (`backend/core-api` — Porta `8080`)**
* **Linguagem & Framework**: **Java 17** com **Spring Boot 3** (Spring Web, Spring Data JPA, Bean Validation, PostgreSQL Driver)
* **Padrão Híbrido**:
  * **Infraestrutura e Persistência**: Controladores REST (`AuthController`, `PerfilController`, `ClinicalController`, `CalculatorController`) e entidades JPA (`user_register`, `farm_history`, `historico_consultas`, `trusted_sources`).
  * **Regras de Negócio e Cálculos Clínicos**: Java 100% Tradicional (`farmCalc.java`, `TokenService.java`).

### **🎨 Frontend (`frontend/` — Porta `3000`)**
* **Stack**: **React 18 + TypeScript (`.tsx`)** com **Vite**
* **Estilização**: CSS3 com variáveis de tema Claro/Escuro e tokens semânticos dos 4 alertas (`danger`, `warning`, `restriction`, `info`)
* **Proxy Integrado**: Roteamento automático no Vite para o `ai-engine` (`5000`) e para a `core-api` (`8080`)

### **🗄️ Banco de Dados & DevOps (`Porta 5432`)**
* **Banco de Dados**: PostgreSQL 16 com extensão `pgvector/pgvector:pg16`
* **Containerização**: Docker & Docker Compose + Makefile

---

## 📂 3. Estrutura de Diretórios do Projeto

```text
C:\workspace\TCC/
├── .env                              # Variáveis de ambiente (Chave GEMINI_API_KEY e banco)
├── .env.example                      # Modelo de variáveis de ambiente
├── package.json                      # Scripts centralizados (npm run dev, check, chat, etc.)
├── Makefile                          # Atalhos para Docker Compose e manutenção do banco
├── docker-compose.yml                # Orquestrador de containers (postgres-db + ai-engine)
├── README.md                         # Documentação principal e guia de comandos
├── GEMINI.md                         # Diretrizes e padrões de arquitetura do projeto
├── Script/
│   └── bulario/                      # Acervo de bulas oficiais da ANVISA em PDF
├── frontend/                         # Interface Web em React + TypeScript (.tsx) + Vite
│   ├── package.json                  # Dependências e scripts do Vite/TypeScript
│   ├── tsconfig.json                 # Configuração do compilador TypeScript
│   ├── vite.config.ts                # Proxy de desenvolvimento (/api -> 8080 e 5000)
│   ├── index.html                    # Entrada HTML raiz
│   └── src/                          # Componentes .tsx, estilos (theme.css) e tipagens
└── backend/
    ├── ai-engine/                    # Motor Python (FastAPI + RAG + PGVector + Gemini)
    │   ├── main.py                   # Ponto de entrada do servidor FastAPI (Porta 5000)
    │   ├── cli_chat.py               # Chat interativo via terminal para testes rápidos
    │   ├── requirements.txt          # Dependências Python
    │   ├── tests/                    # Testes unitários (Guardrail, Prompt Sanduíche, IMC, RAG)
    │   └── app/                      # Camadas: api/, db/ (models, session, seed), schemas/, services/
    └── core-api/                     # Servidor Java 17 (Spring Boot 3 — Porta 8080)
        ├── pom.xml                   # Configuração Maven e dependências
        └── src/main/java/com/medinteract/coreapi/
            ├── controller/           # Auth, Perfil, Clinical, Calculator e Health Controllers
            ├── model/                # Entidades User (user_register), FarmHistory, UserHistory
            ├── repository/           # Repositórios Spring Data JPA
            └── service/              # Cálculos clínicos em Java Tradicional (farmCalc, TokenService)
```

---

## 🗺️ 4. Status dos Ciclos de Desenvolvimento

| Ciclo | Descrição | Status |
| :--- | :--- | :---: |
| **Ciclo 1** | Preparação do Banco (`PGVector` + HNSW) e Script Resiliente de Ingestão de Bulas (`seed.py`) | 🟢 Concluído |
| **Ciclo 2** | Motor de IA e RAG no FastAPI (Guardrails, Prompt Sanduíche, Streaming SSE e Fallback Seguro) | 🟢 Concluído |
| **Ciclo 3** | Core API Java — Autenticação (`user_register`) e Ficha Clínica (`farm_history`) por `UUID` | 🟢 Concluído |
| **Ciclo 4** | Core API Java — Orquestração com Python e Calculadoras Farmacêuticas (`farmCalc`) | 🟢 Concluído |
| **Ciclo 5** | Frontend em React + TypeScript (`.tsx`), Tema Claro/Escuro, Login, Ficha Clínica e Streaming | ⏳ Em Andamento |
| **Ciclo 6** | Alertas Visuais, Telas de Calculadoras, Impressão de Laudo e Dockerização Final | 📋 Planejado |

---

## ⚡ 5. Guia Completo de Comandos do Projeto

Todos os comandos abaixo devem ser executados na **raiz do projeto (`C:\workspace\TCC`)**.

### 🚀 5.1. Comandos de Execução (`npm run`)

| Comando | O que faz |
| :--- | :--- |
| **`npm run dev`** | **Inicia o programa completo de uma só vez**: sobe o container `postgres-db` (`5432`), inicia o Backend Python (`5000`), o Backend Java (`8080`) e o Frontend React/Vite (`3000`). Ao apertar `Ctrl + C`, encerra os servidores automaticamente. |
| **`npm run dev:python`** | Inicia apenas o servidor **Backend Python (`ai-engine` FastAPI)** na porta `5000`. |
| **`npm run dev:java`** | Inicia apenas o servidor **Backend Java (`core-api` Spring Boot 3)** na porta `8080`. |
| **`npm run dev:frontend`** | Inicia apenas o servidor de desenvolvimento do **Frontend (Vite + React)** na porta `3000`. |
| **`npm run chat`** | Abre o **Chat Interativo direto no Terminal** para conversar e testar perguntas no Gemini + RAG sem precisar abrir o navegador. |

```powershell
# Executar todo o ecossistema (Banco + Python + Java + Frontend)
npm run dev

# Ou iniciar cada serviço individualmente em terminais separados:
npm run dev:python
npm run dev:java
npm run dev:frontend

# Testar perguntas à IA diretamente pelo console/terminal:
npm run chat
```

---

### ✅ 5.2. Comandos de Verificação, Testes e Build (`npm run`)

| Comando | O que faz |
| :--- | :--- |
| **`npm run check`** | **Validação completa**: executa em sequência `check:python`, `check:java` e `check:frontend`. |
| **`npm run check:python`** | Verifica a sintaxe (`py_compile`) dos módulos principais do `ai-engine`. |
| **`npm run check:java`** | Compila todas as classes Java 17 e testes da `core-api` via Maven (`test-compile`). |
| **`npm run check:frontend`** | Valida toda a tipagem TypeScript (`.tsx`) do Frontend com `tsc --noEmit`. |
| **`npm run test:python`** | Executa a suíte de testes unitários do Python (`Guardrail`, `Prompt Sanduíche`, `Sanitização XML`, `IMC` e `RAG`). |
| **`npm run build:java`** | Gera o pacote `.jar` de produção da `core-api` em `backend/core-api/target/`. |

```powershell
# Rodar todas as checagens (Python + Java + Frontend) de uma vez:
npm run check

# Rodar os testes unitários do motor Python:
npm run test:python

# Empacotar o .jar do Backend Java:
npm run build:java
```

---

### 🗄️ 5.3. Comandos do Banco de Dados e Ingestão de Bulas (`seed.py`)

Para vetorizar as bulas em PDF da pasta `Script/bulario/` no PostgreSQL (`bula_chunks`):

```powershell
# Subir apenas o banco de dados PostgreSQL + PGVector no Docker
docker compose up -d postgres-db

# Rodar o seed padrão (primeiras 9 bulas prioritárias com controle de rate-limit)
python -m app.db.seed

# Ou executar a partir da raiz especificando limite de PDFs e teto de chunks:
python backend/ai-engine/app/db/seed.py --limit 20 --max-chunks 850 --batch-size 20

# Processar todas as bulas do diretório Script/bulario/ (respeitando o teto de chunks por rodada):
python backend/ai-engine/app/db/seed.py --limit 0 --max-chunks 850
```

---

### 🐳 5.4. Comandos Docker Compose e `Makefile`

```powershell
# Subir banco de dados e ai-engine em background via Docker Compose
docker compose up -d

# Reconstruir imagens e subir containers
docker compose up --build -d

# Parar todos os containers
docker compose down

# Abrir o terminal SQL (psql) diretamente dentro do banco medinteract
docker compose exec postgres-db psql -U postgres -d medinteract
```

Caso utilize a ferramenta `make` (configurada no [`Makefile`](file:///C:/workspace/TCC/Makefile)):
* `make up` — Sobe os containers em segundo plano (`docker-compose up -d`)
* `make down` — Desliga os containers (`docker-compose down`)
* `make build` — Reconstrói e sobe os containers (`docker-compose up --build -d`)
* `make log` — Exibe os logs em tempo real (`docker-compose logs -f`)
* `make dataBase` — Abre o console interativo `psql` no banco `medinteract`
* `make seed` — Executa a vetorização de bulas dentro do container `ai-engine`
* `make clean` — Remove pastas temporárias `__pycache__`

---

## 🌐 6. Endereços e Portas dos Serviços Locais

Quando a aplicação estiver em execução (`npm run dev`), acesse:

| Serviço | Endereço Local | Descrição |
| :--- | :--- | :--- |
| **🎨 Frontend (React + Vite)** | `http://localhost:3000` | Interface gráfica principal do usuário |
| **☕ Core API Java (Health)** | `http://localhost:8080/api/core/health` | Status da API Spring Boot 3, Login, Ficha Clínica e Calculadoras |
| **🐍 AI Engine Python (Swagger)** | `http://localhost:5000/docs` | Documentação interativa (Swagger UI) para testar o Gemini e o RAG |
| **🐍 AI Engine Python (Health)** | `http://localhost:5000/api/health` | Status do servidor FastAPI |
| **🗄️ PostgreSQL + PGVector** | `localhost:5432` | Banco `medinteract` (usuário: `postgres` / senha: `postgrespassword`) |

---

## 🚨 7. Padronização de Alertas na Interface (`alert_type`)

Todas as respostas clínicas e tratativas de erro retornam um `alert_type` padronizado para renderização visual na UI:

* **`danger`** (Vermelho): Interação medicamentosa grave, contraindicação formal ou erro crítico.
* **`warning`** (Amarelo): Uso com cautela, necessidade de monitoramento clínico ou ajuste de dose.
* **`restriction`** (Laranja/Restrição): **Fallback Seguro de Saúde** ativado quando a IA está indisponível, exibindo links oficiais da ANVISA e Medscape.
* **`info`** (Azul): Orientações educativas, ausência de interação relatada em bula ou bloqueio educativo de fuga de escopo.

---

## 👤 Autores

* **Kauã Ricardo de Castro Galvão**
* **Sofia David de Carvalho**

*Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC).*
