# 🏛️ MEDINTERACT - ARQUITETURA DE MICROSSERVIÇOS POLIGLOTA & PLANEJAMENTO TÉCNICO

> **Projeto de Conclusão de Curso (TCC)**  
> **Tema**: Plataforma Farmacológica de Análise de Interações Medicamentosas, Dosagens e Bulário Inteligente  
> **Padrão de Arquitetura**: Microsserviços Poliglota (Java 17 + Python 3.10+ + PGVector)  
> **Data de Atualização**: 03/09/2026  

---

## 🎯 1. Visão Geral da Arquitetura

O sistema MedInteract adota uma **Arquitetura de Microsserviços Poliglota**, explorando o ponto forte de cada tecnologia:
* **Java 17 (Spring Boot 3)**: Responsável pelo núcleo corporativo da aplicação, controle de acesso, regras de negócio clínicas determinísticas e orquestração.
* **Python 3.10+ (FastAPI)**: Responsável pelo motor de Inteligência Artificial, extração de dados não-estruturados (PDFs com `pdfplumber`), vetorização semântica (Embeddings) e RAG (*Retrieval-Augmented Generation*).
* **PostgreSQL 16 com PGVector**: Banco de dados unificado de alta performance que suporta tanto tabelas relacionais clássicas quanto armazenamento e consulta vetorial por similaridade de cosseno (`vector(768)`).

---

## 🏗️ 2. Nomenclatura Profissional e Estrutura de Diretórios

Seguindo os princípios de *Domain-Driven Design* (DDD) e padrões internacionais de microsserviços, os módulos são nomeados por sua **responsabilidade de negócio**, e não pelo nome da linguagem de programação.

```text
C:\workspace\TCC\
├── backend/
│   ├── ai-engine/                  # [Python 3.10+ / FastAPI] - Motor de IA e Vetores
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   └── pdfreader/      # Extração e chunking de bulas (pdfplumber)
│   │   │   ├── db/
│   │   │   │   ├── models.py       # Tabela bula_chunks com Vector(768)
│   │   │   │   └── session.py      # Conexão assíncrona SQLAlchemy
│   │   │   ├── services/
│   │   │   │   ├── embedding_service.py # Google Gemini text-embedding-004
│   │   │   │   └── rag_service.py       # Busca por similaridade vetorial
│   │   │   ├── config.py           # Variáveis de ambiente (.env)
│   │   │   └── utils/
│   │   │       └── logger.py       # Logging estruturado
│   │   ├── main.py                 # API interna FastAPI (Porta 5000)
│   │   ├── requirements.txt        # Dependências Python
│   │   └── Dockerfile              # Container Docker do motor de IA
│   │
│   └── core-api/                   # [Java 17 / Spring Boot 3] - Núcleo de Negócio (Fase 2)
│       ├── src/main/java/com/medinteract/core/
│       │   ├── controllers/        # Endpoints REST públicos da aplicação
│       │   ├── services/           # Lógica clínica, orquestração e clientes HTTP
│       │   ├── models/             # Entidades relacionais (Users, History)
│       │   └── clients/            # WebClient de comunicação com o ai-engine
│       ├── pom.xml                 # Gerenciador Maven
│       └── Dockerfile              # Container Docker da aplicação Java
│
├── Script/
│   └── bulario/                    # Acervo oficial das 245 bulas da ANVISA em PDF
├── Support/
│   ├── Modelo Projeto/             # Diagramas e fluxogramas de referência
│   └── docs/                       # Documentações técnicas auxiliares
├── ARQUITETURA_E_PLANEJAMENTO.md   # Este documento mestre de arquitetura
└── docker-compose.yml              # Orquestrador unificado de containers
```

---

## 🔄 3. Fluxo de Comunicação e Responsabilidades

```text
[Usuário / Cliente / Frontend Futuro]
                  │
                  │ Requisições HTTP Públicas
                  ▼
┌──────────────────────────────────────────────────────────────┐
│                  backend/core-api (Java 17)                  │
│                      "O Cérebro de Negócio"                  │
│                                                              │
│  - Porta: 8080                                               │
│  - Gateway e Autenticação de Usuários                        │
│  - Definição do Perfil Clínico (PROFESSIONAL vs PATIENT)     │
│  - Calculadoras farmacêuticas determinísticas                │
│  - Histórico de consultas e auditoria                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ Chamada HTTP Interna (JSON)
                               │ POST /api/ai/query
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 backend/ai-engine (Python)                   │
│                   "O Motor de IA e Bulas"                    │
│                                                              │
│  - Porta: 5000 (Rede Interna Docker)                         │
│  - Leitura e Chunking dos PDFs (pdfProcess.py)               │
│  - Geração de Vetores de 768 dimensões (text-embedding-004) │
│  - Consulta Semântica no PGVector (<=>)                      │
│  - Injeção de Contexto Oficial no Prompt da IA               │
│  - Retorno de Resposta Estruturada + Fontes Confiáveis       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ SQL & Operações Vetoriais
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    PostgreSQL 16 + PGVector                  │
│  - Tabelas Relacionais: users, user_history, trusted_sources │
│  - Tabela Vetorial: bula_chunks (id, content, embedding)     │
└──────────────────────────────────────────────────────────────┘
```

---

## 📅 4. Roteiro de Execução em Fases

### 📍 Fase 1 (ATUAL): O Motor de IA e Dados (`ai-engine`)
> **Objetivo**: Garantir que o pipeline de leitura, vetorização e recuperação de bulas esteja 100% funcional e testado antes de construir os consumidores.
1. **Passo 1 (Concluído)**: Processamento e fatiamento das bulas em PDF com `pdfplumber` (`pdfProcess.py`).
2. **Passo 2 (Em andamento)**: Criação do serviço de Embeddings com Gemini (`embedding_service.py`).
3. **Passo 3**: Script de povoamento/ingestão no PostgreSQL (`bula_chunks` no PGVector).
4. **Passo 4**: Serviço de busca por similaridade semântica (`rag_service.py`).
5. **Passo 5**: Endpoint interno `POST /api/ai/query` respondendo com base nas bulas oficiais.

### 📍 Fase 2: O Núcleo da Aplicação (`core-api` em Java)
> **Objetivo**: Implementar o Spring Boot 3 para orquestrar as regras de negócio e servir como entrada pública.
1. Inicialização do projeto Spring Boot 3 com Java 17 no diretório `backend/core-api/`.
2. Criação do cliente HTTP (`WebClient` ou `RestClient`) para se comunicar com o `ai-engine`.
3. Modelagem de dados relacionais e histórico no PostgreSQL.
4. Regras clínicas, cálculo de posologia e perfis de usuário (`PROFESSIONAL` vs `PATIENT`).

### 📍 Fase 3: Integração & Containerização
> **Objetivo**: Integrar os microsserviços via Docker Compose e preparar para testes finais e frontend.
1. Orquestração completa no `docker-compose.yml` (`postgres-db`, `ai-engine`, `core-api`).
2. Testes de ponta a ponta com casos reais de interação medicamentosa.
3. Defesa do TCC com arquitetura poliglota validada.
