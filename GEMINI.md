# 🛡️ Diretrizes e Padrão do Projeto MedInteract

Sempre que uma nova conversa for iniciada neste repositório (`C:\workspace\TCC`), siga estritamente as diretrizes e os planos acordados para este projeto.

## 📄 Documentos de Referência Obrigatórios

1. **Relatório Mestre de Arquitetura & Padrão do Projeto**:
   - [`support/docs/backend_architecture_plan.md`](file:///C:/workspace/TCC/support/docs/backend_architecture_plan.md)
   - Contém a estrutura oficial de pastas do FastAPI, schemas Pydantic, Fallback Seguro, System Prompt Adaptativo (`PROFESSIONAL` vs `PATIENT`), mapeamento de alertas da UI (`alert_type`) e esquema de tabelas (`perfil_usuario`, `bula_chunks`, `historico_consultas`, `trusted_sources`).

2. **Relatório Técnico de Viabilidade e Roteiro de Execução**:
   - [`support/docs/projeto_medinteract_relatorio_viabilidade.md`](file:///C:/workspace/TCC/support/docs/projeto_medinteract_relatorio_viabilidade.md)
   - Contém o nível de dificuldade, dependências (`pdfplumber`, `pgvector`, `fastapi`, `httpx`), pré-requisitos e o roteiro detalhado em 5 Etapas ("O Que Faremos e Como").

3. **Especificação de Perfil Clínico Anônimo (Privacy by Design) e Prompt Sanduíche**:
   - [`c:\workspace\Relatório tcc\UserMolde\Alterações e Modelagens necessárias!.md`](file:///c:/workspace/Relat%C3%B3rio%20tcc/UserMolde/Altera%C3%A7%C3%B5es%20e%20Modelagens%20necess%C3%A1rias%21.md)
   - Define o modelo sem senhas/dados sensíveis (identificação via `UUID v4` no `localStorage`), tabelas `perfil_usuario` e `historico_consultas`, sanitização XML (`.`replace("<", "").replace(">", "")`), cálculo de IMC no backend e Template Oficial do Prompt Sanduíche.

4. **Relatório de Progresso e Ponto de Retomada**:
   - [`c:\workspace\Relatório tcc\RELATORIO_PROGRESSO_E_RETOMADA.md`](file:///c:/workspace/Relat%C3%B3rio%20tcc/RELATORIO_PROGRESSO_E_RETOMADA.md)
   - Resumo completo dos Ciclos 1 a 4 concluídos, métodos criados no Java e Python, e ponto exato de retomada (Ciclo 5 — Card 5.1).

5. **Diagramas de Referência**:
   - Diretório `Modelo Projeto/` contendo o fluxo de pipeline RAG, vetorização no `PGVector`, extração com `pdfplumber` e schemas originais do usuário.

## 🎯 Regras de Código e Arquitetura

- **Stack Backend Python (`ai-engine`)**: Python 3.10+, FastAPI (assíncrono), Pydantic v2, Uvicorn, HTTPX, SQLAlchemy 2.0 (Async), PGVector.
- **Stack Backend Java (`core-api`)**: Java 17, Spring Boot 3 (Web, Data JPA, Validation, PostgreSQL Driver) — **Sem Spring Security/JJWT** (Privacy by Design via `UUID v4`).
- **Padrão Híbrido no Java**:
  - **Lógica de Negócio e Cálculos Clínicos** (ex: `farmCalc.java`): Escrever em **Java 100% Tradicional** (classes comuns, sem `@`, instanciadas com `new`).
  - **Conexões de Rede e Banco** (`Controller`, `Model`, `Repository`): Usar anotações (`@RestController`, `@Entity`, etc.) para evitar código verboso de infraestrutura.
- **Padrão de Comentários no Código**: Nunca espalhar blocos longos de comentários. Usar apenas comentários curtos, simples e explicativos de **no máximo 1 ou 2 linhas** (preferencialmente apenas `//` no Java e `#` no Python).
- **Comunicação de IA**: Suporte a Streaming SSE (`/api/chat/stream`) e resposta JSON estruturada (`/api/ai/query`) usando o **Prompt Sanduíche**.
- **Fallback Seguro**: Nunca inventar simulações fictícias se a IA falhar; responder com `alert_type: "restriction"` e links oficiais pré-aprovados.
- **Formato de Erro na UI**: Todos os erros devem conter `alert_type` (`"danger"`, `"warning"`, `"restriction"`, `"info"`).

## 📌 Rastreamento Obrigatório de Tarefas e Validação de Etapas

Antes de iniciarmos a próxima tarefa pedida, SEMPRE exiba qual tarefa e etapa exata estamos de acordo com o arquivo no endereço: `\workspace\Relatório tcc\tasks/ tasks.md`

Deve-se enviar junto com a confirmação da leitura deste arquivo um relatório básico indicando: A tarefa que estamos, card, etapa e o que faremos.
Enviar também PARA COMPROVAÇÃO DE LEITURA um código que será SEMPRE o valor do card+14.03 Exemplo: card 6.4 -> 6.4 + 14.03 = 20.07
