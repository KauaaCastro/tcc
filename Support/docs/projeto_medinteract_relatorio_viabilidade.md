# 📊 Relatório Técnico de Viabilidade, Complexidade e Roteiro de Execução (MedInteract)

> **Objetivo**: Avaliação honesta do nível de dificuldade do projeto, levantamento de requisitos/ferramentas necessárias e guia detalhado de execução ("O Que Faremos e Como").

---

## ⚖️ 1. Avaliação de Complexidade e Dificuldade

### **Nível Geral de Dificuldade: Média a Avançada (7.5 / 10)**

#### 🟢 Por que o projeto É TOTALMENTE VIÁVEL e Alcance de Sucesso é Alto?
1. **Modelos de IA Estado da Arte**: Não estamos criando ou treinando um modelo de linguagem do zero (o que seria extremamente difícil e demorado). Estamos consumindo APIs potentes (Gemini 1.5 Flash / Claude) que já entendem português e medicina.
2. **Padrão RAG Consagrado**: A técnica de **RAG (Retrieval-Augmented Generation)** que utilizaremos é o padrão de mercado mais moderno e confiável para evitar alucinações de IA em sistemas de saúde.
3. **Stack Moderna**: O **FastAPI** e o **Pydantic** eliminam mais de 50% dos erros comuns de backend em Python através de tipagem e validação automáticas.

#### ⚠️ Quais são os 3 Maiores Desafios Técnicos do Projeto?
1. **Leitura e Limpeza de PDFs (`pdfplumber`)**: Bulas de remédios em PDF têm layouts complexos (colunas, tabelas, fontes pequenas). Precisaremos garimpar o texto com cuidado para gerar *chunks* limpos.
2. **Busca Vetorial no PGVector**: Configurar os *embeddings* numéricos e a extensão `pgvector` no PostgreSQL via Docker para realizar buscas por similaridade semântica em milissegundos.
3. **Transmissão em Streaming (SSE)**: Garantir que a resposta seja enviada palavra a palavra para a interface gráfica sem perda de pacotes ou desconexões.

---

## 📦 2. O Que Será Necessário (Pré-requisitos e Ferramentas)

### A. Ferramentas de Software
* **Python 3.10+** (Ambiente local de execução).
* **Docker Desktop & Docker Compose** (Para rodar o banco de dados PostgreSQL com PGVector e a aplicação).
* **Git** (Controle de versão).

### B. Dependências & Bibliotecas Python (`requirements.txt`)
* **`fastapi`** & **`uvicorn[standard]`**: Framework web assíncrono e servidor HTTP.
* **`pydantic`** & **`pydantic-settings`**: Validação de dados (DTOs) e leitura de variáveis de ambiente.
* **`httpx`**: Cliente HTTP assíncrono para chamada das APIs de IA.
* **`pdfplumber`**: Biblioteca para extração limpa de texto de PDFs de bulas.
* **`sqlalchemy`**, **`asyncpg`**, **`pgvector`**: ORM assíncrono para conexão com o banco PostgreSQL de vetores.
* **`python-dotenv`**: Carregamento do arquivo `.env`.

### C. Contas & Chaves de API
* **Google Gemini API Key** (`GEMINI_API_KEY`): Gratuita via Google AI Studio (Usada para geração de respostas e embeddings).
* **Anthropic Claude API Key** (`ANTHROPIC_API_KEY`): Opcional, para redundância.

---

## 🛠️ 3. Relatório Detalhado: "O Que Faremos e Como"

O projeto será construído em **5 Etapas Claras e Sequenciais**:

```text
Etapa 1: Base do Backend & Engine de IA
 └── Etapa 2: Processamento de Bulas & pdfplumber
      └── Etapa 3: Banco de Dados Vetorial & RAG
           └── Etapa 4: Guardrails & Perfis de Usuário
                └── Etapa 5: Conexão com Frontend & Docker
```

---

### 🔹 ETAPA 1: Fundação do Backend & Motor de IA com Streaming
* **O Que Faremos**: Criar a estrutura física de pastas no formato por camadas (`app/api`, `app/schemas`, `app/services`), o arquivo `config.py` e o orquestrador de IA assíncrono.
* **Como Faremos**:
  1. Instanciar o servidor FastAPI em `main.py`.
  2. Criar os Schemas Pydantic em `app/schemas/chat.py` e `app/schemas/error.py`.
  3. Implementar o `AIService` em `app/services/ai_service.py` que tenta o Gemini, depois Claude, e se nenhum funcionar, dispara o **Fallback Seguro** com alertas em JSON e links confiáveis.
  4. Adicionar a rota de streaming via Server-Sent Events (`StreamingResponse`).

### 🔹 ETAPA 2: Processamento de Bulas em PDF (`pdfplumber`)
* **O Que Faremos**: Criar o script leitor que abre os arquivos de bula em PDF da pasta `Script/`, extrai o texto e o divide em blocos menores (*chunks*).
* **Como Faremos**:
  1. Criar o serviço `app/services/pdf_processor.py`.
  2. Usar `pdfplumber.open(pdf_path)` para extrair o texto limpo página a página.
  3. Aplicar um algoritmo de divisão de texto (Chunking) dividindo a bula em blocos de ~800 caracteres com sobreposição (overlap) para manter o contexto farmacológico de cada seção (Indicações, Posologia, Contraindicações).

### 🔹 ETAPA 3: Banco de Dados Vetorial (PostgreSQL + PGVector) & Pipeline RAG
* **O Que Faremos**: Subir o banco de dados PostgreSQL com extensão `pgvector` e criar as tabelas `Users`, `Bula_Chunks` e `User_History`.
* **Como Faremos**:
  1. Configurar a imagem `ankane/pgvector` no `docker-compose.yml`.
  2. Criar os modelos SQLAlchemy em `app/db/models/`.
  3. Desenvolver o `rag_service.py`: Quando o usuário faz uma pergunta, o serviço converte a pergunta em um vetor numérico (Embedding), faz uma consulta de similaridade cosseno (`<->`) na tabela `Bula_Chunks` e recupera os 3 a 5 trechos mais relevantes da bula.
  4. Injetar esses trechos resgatados dentro do Prompt Mestre enviado para a IA.

### 🔹 ETAPA 4: Guardrails (Fuga de Assunto) & Adaptação ao Perfil do Usuário
* **O Que Faremos**: Garantir que a plataforma recuse responder perguntas fora do tema médico/farmacológico (ex: receitas culinárias, futebol) e adaptar o tom da resposta segundo o perfil do usuário.
* **Como Faremos**:
  1. Criar um validador de escopo (`scope_checker.py`). Se a pergunta fugir do assunto, a API responde imediatamente com `alert_type: "restriction"` ou `"warning"`.
  2. No `prompt_service.py`, injetar regras distintas no prompt:
     * Se `profile_type == "PROFESSIONAL"`: Resposta em linguagem clínica/farmacológica estrita (mecanismo CYP, RNI, farmacocinética).
     * Se `profile_type == "PATIENT"`: Resposta em linguagem simples, direta e empática, alertando para a importância de consultar um médico.

### 🔹 ETAPA 5: Conexão com o Frontend & Dockerização Final
* **O Que Faremos**: Conectar a interface web aos novos endpoints assíncronos e empacotar a aplicação inteira em Docker.
* **Como Faremos**:
  1. Atualizar o arquivo [`frontend/js/app.js`](file:///C:/workspace/TCC/frontend/js/app.js) para ler o fluxo de streaming de texto usando `ReadableStreamReader` do navegador.
  2. Atualizar o `nginx.conf` e testar a subida completa com `docker-compose up --build`.
