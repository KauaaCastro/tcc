# ⚕️ MedInteract — Plataforma de Análise de Interações Medicamentosas com IA & RAG

> **Trabalho de Conclusão de Curso (TCC)**  
> **Autores**: Kauã Ricardo de Castro Galvão & Sofia David de Carvalho  
> **Instituição**: Plataforma Web de Suporte à Decisão Farmacológica Clínica

---

## 📌 1. Sobre o Projeto

O **MedInteract** é uma plataforma web inteligente desenvolvida para realizar análises de interações medicamentosas, fornecendo suporte à decisão clínica para profissionais de saúde (farmacêuticos, médicos e enfermeiros) e orientações didáticas e seguras para pacientes e usuários comuns.

A plataforma combina a potência dos modelos de linguagem de última geração (LLMs) com a técnica de **RAG (Retrieval-Augmented Generation)**, realizando buscas por similaridade semântica em bulas oficiais da ANVISA armazenadas em um banco de dados vetorial (**PGVector**).

### 🎯 Principais Diferenciais
* **Perfil Adaptativo**: Respostas em linguagem técnica médica para profissionais (`PROFESSIONAL`) ou linguagem simplificada e acessível para pacientes (`PATIENT`).
* **Streaming em Tempo Real (SSE)**: Transmissão da análise palavra por palavra via Server-Sent Events, reduzindo o tempo de espera percebido.
* **Fallback Seguro de Saúde**: Caso as IAs estejam indisponíveis, o sistema **não gera simulações médicas arbitrárias**; em vez disso, aciona um mecanismo de restrição que exibe links e fontes oficiais pré-aprovadas (ANVISA, PubChem, Medscape, etc.).
* **Guardrails de Escopo**: Bloqueio automático de perguntas fora do contexto médico/farmacológico (prevenção de fuga de assunto).

---

## 🛠️ 2. Arquitetura e Tecnologias Utilizadas

### **Backend (Servidor & APIs)**
* **Linguagem**: Python 3.10+
* **Framework Web**: **FastAPI** (Assíncrono, OpenAPI Swagger em `/docs`)
* **Validação de Dados & DTOs**: **Pydantic v2**
* **Servidor ASGI**: **Uvicorn**
* **ORM & Banco de Dados**: **SQLAlchemy 2.0 (Async)** com suporte a **PGVector** (PostgreSQL) e SQLite (Dev Local)
* **Processamento de PDFs**: **`pdfplumber`** (Extração limpa de texto de bulas em PDF)
* **Cliente HTTP Assíncrono**: **HTTPX**

### **Inteligência Artificial & RAG**
* **Provedor Principal**: Google Gemini API (`gemini-1.5-flash` + Text Embeddings)
* **Provedor Secundário**: Anthropic Claude API (`claude-3-5-sonnet`)
* **Busca Vetorial**: PGVector (PostgreSQL) para similaridade de cosseno em chunks de bulas

### **Frontend (Interface do Usuário)**
* **Core**: Vanilla HTML5 e JavaScript ES6+ (Arquitetura SPA)
* **Estilização**: Vanilla CSS3 com tokens de design, vidro fosco (glassmorphism), temas escuro/claro e layouts responsivos
* **Consumo de API**: Fetch API com leitor de stream em tempo real (`ReadableStreamReader`)

### **DevOps & Infraestrutura**
* **Containerização**: Docker & Docker Compose
* **Proxy Reverso**: Nginx (para roteamento transparente da API e frontend na porta `80`)

---

## 📂 3. Estrutura de Diretórios do Projeto

```text
C:\workspace\TCC/
├── .env                              # Variáveis de ambiente (Chaves de API)
├── .env.example                      # Modelo de variáveis de ambiente
├── .gitignore                        # Regras de exclusão do Git
├── README.md                         # Documentação principal do repositório
├── GEMINI.md                         # Diretrizes automáticas de contexto do projeto
├── docker-compose.yml                # Orquestrador de containers Docker
├── docs/                             # Documentos e relatórios de arquitetura
│   ├── backend_architecture_plan.md  # Plano Mestre de Arquitetura e Schemas DTO
│   └── projeto_medinteract_relatorio_viabilidade.md # Relatório de Viabilidade e Roteiro
├── Modelo Projeto/                   # Diagramas visuais de banco, RAG e fluxos de dados
│   ├── IMG-20260413-WA0011.jpg       # Diagrama de Arquitetura Geral
│   ├── IMG-20260413-WA0012.jpg       # Modelo Relacional das Tabelas
│   └── IMG-20260413-WA0015.jpg       # Fluxo de Armazenamento e Ingestão de Bulas
├── Script/                           # Scripts de raspagem e automação de bulas
│   └── Script Python/                # Scripts Python para download de PDFs da ANVISA
├── frontend/                         # Interface do Usuário
│   ├── Dockerfile                    # Container Nginx para servir a interface
│   ├── index.html                    # Estrutura HTML principal
│   ├── nginx.conf                    # Configuração de proxy reverso (/api)
│   ├── css/style.css                 # Tokens de design e estilos
│   └── js/app.js                     # Lógica da aplicação web e leitor de SSE
└── backend/                          # Servidor FastAPI
    ├── Dockerfile                    # Container Python + Uvicorn
    ├── main.py                       # Ponto de entrada da aplicação FastAPI
    ├── requirements.txt              # Dependências Python
    └── app/                          # Arquitetura por Camadas
        ├── config.py                 # Leitura de .env via Pydantic BaseSettings
        ├── api/                      # Camada de Controladores / Rotas
        │   ├── router.py             # Agregador de rotas
        │   └── endpoints/            # Chat (/api/chat), Health (/api/health), etc.
        ├── schemas/                  # DTOs Pydantic (Chat, Erros, Usuário, Calculadoras)
        ├── services/                 # Regras de negócio (AIService, RAGService, PromptService)
        ├── db/                       # Sessão SQLAlchemy e Tabelas (Users, Bula_Chunks, User_History)
        └── utils/                    # Helpers (SSE e Logging)
```

---

## 🗺️ 4. Etapas de Execução do Desenvolvimento

O desenvolvimento do projeto é conduzido em **5 Etapas Sequenciais**:

| Etapa | Descrição | Status |
| :--- | :--- | :---: |
| **Fase 0** | Planejamento Mestre, Arquitetura por Camadas e Documentação | 🟢 Concluído |
| **Etapa 1** | Fundação do Backend FastAPI, Schemas Pydantic, Engine de IA & Streaming SSE | ⏳ Em Andamento |
| **Etapa 2** | Processamento de Bulas em PDF com `pdfplumber` e Gerador de Chunks | 📋 Planejado |
| **Etapa 3** | Banco de Dados Vetorial (PostgreSQL + PGVector) e Pipeline RAG | 📋 Planejado |
| **Etapa 4** | Validador de Escopo (Fuga de Assunto) e Adaptação de Perfil (`PROFESSIONAL` vs `PATIENT`) | 📋 Planejado |
| **Etapa 5** | Conexão com Frontend, Emissão de Laudos e Dockerização Final | 📋 Planejado |

---

## 🚨 5. Padronização de Alertas e Erros na UI

Para garantir uma experiência de usuário uniforme, todas as respostas de erro da API seguem uma estrutura padronizada contendo a classificação do alerta na interface:

```json
{
  "error": {
    "code": "AI_SERVICE_UNAVAILABLE",
    "title": "Serviço Indisponível",
    "message": "Os serviços de Inteligência Artificial estão temporariamente indisponíveis.",
    "alert_type": "restriction",
    "status_code": 503,
    "timestamp": "2026-08-11T21:35:00Z",
    "links": [
      { "name": "Bulário Eletrônico da ANVISA", "url": "https://consultas.anvisa.gov.br/#/bulario/" }
    ]
  }
}
```

* **`danger`**: Falhas críticas de rede ou servidor (500).
* **`warning`**: Erros de validação de formulário ou dados incompletos (400/422).
* **`restriction`**: Fallback seguro ativado por ausência de IA, exibindo fontes externas oficiais.
* **`info`**: Avisos educativos e informativos gerais.

---

## 🚀 6. Como Executar o Projeto

### **Pré-requisitos**
* [Docker Desktop](https://www.docker.com/) e Docker Compose instalados.
* [Python 3.10+](https://www.python.org/) (opcional para rodar sem Docker).

### **Passo 1: Configurar Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto (baseando-se no `.env.example`):
```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio_aqui
ANTHROPIC_API_KEY=sua_chave_opcional_aqui
PORT=5000
```

### **Passo 2: Subir a Aplicação via Docker**
No terminal, execute:
```bash
docker-compose up --build
```

### **Passo 3: Acessar a Plataforma**
Abra o navegador no endereço:  
👉 **`http://localhost`** (Interface Gráfica)  
👉 **`http://localhost:5000/docs`** (Documentação Interativa da API Swagger)

---

## 👤 Autores

* **Kauã Ricardo de Castro Galvão**
* **Sofia David de Carvalho**

*Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC).*
