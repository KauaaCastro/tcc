# 🛡️ Diretrizes e Padrão do Projeto MedInteract

Sempre que uma nova conversa for iniciada neste repositório (`C:\workspace\TCC`), siga estritamente as diretrizes e os planos acordados para este projeto.

## 📄 Documentos de Referência Obrigatórios

1. **Relatório Mestre de Arquitetura & Padrão do Projeto**:
   - [`support/docs/backend_architecture_plan.md`](file:///C:/workspace/TCC/support/docs/backend_architecture_plan.md)
   - Contém a estrutura oficial de pastas do FastAPI, schemas Pydantic, Fallback Seguro, System Prompt Adaptativo (`PROFESSIONAL` vs `PATIENT`), mapeamento de alertas da UI (`alert_type`) e esquema de tabelas (`Users`, `Bula_Chunks`, `User_History`, `TrustedSource`).

2. **Relatório Técnico de Viabilidade e Roteiro de Execução**:
   - [`support/docs/projeto_medinteract_relatorio_viabilidade.md`](file:///C:/workspace/TCC/support/docs/projeto_medinteract_relatorio_viabilidade.md)
   - Contém o nível de dificuldade, dependências (`pdfplumber`, `pgvector`, `fastapi`, `httpx`), pré-requisitos e o roteiro detalhado em 5 Etapas ("O Que Faremos e Como").

3. **Diagramas de Referência**:
   - Diretório `Modelo Projeto/` contendo o fluxo de pipeline RAG, vetorização no `PGVector`, extração com `pdfplumber` e schemas originais do usuário.

## 🎯 Regras de Código e Arquitetura

- **Stack Backend**: Python 3.10+, FastAPI (assíncrono), Pydantic v2, Uvicorn, HTTPX, SQLAlchemy 2.0 (Async), PGVector.
- **Estrutura de Pastas**: Arquitetura por Camadas (`app/api`, `app/schemas`, `app/services`, `app/db`, `app/utils`).
- **Comunicação de IA**: Suporte a Streaming SSE via Server-Sent Events.
- **Fallback Seguro**: Nunca inventar simulações fictícias se a IA falhar; responder com `alert_type: "restriction"` e links oficiais pré-aprovados.
- **Formato de Erro na UI**: Todos os erros devem conter `alert_type` (`"danger"`, `"warning"`, `"restriction"`, `"info"`).
