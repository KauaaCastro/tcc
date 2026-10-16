# ☕ MedInteract Core API (Java 17 / Spring Boot 3)

Backend Java responsável pelo gerenciamento do **Perfil Clínico Anônimo (UUID v4)**, **Histórico de Consultas**, **Calculadoras Farmacêuticas Determinísticas** e **Orquestração com o Motor de IA (`ai-engine`)**.

---

## 🏛️ Padrão Arquitetural Adotado

1. **Privacy by Design (Zero Senha / Zero Dados Sensíveis)**:
   - O sistema não coleta e-mail, CPF, CRM ou senhas.
   - O usuário é identificado exclusivamente por um `UUID v4` gerado pelo navegador (`localStorage`).
2. **Arquitetura Híbrida (Java Tradicional + Anotações de Conexão)**:
   - **Regras de Negócio e Cálculos (`service/`)**: Escritos em **Java 100% Tradicional** (classes comuns sem `@`, instanciadas com `new`).
   - **Conexões HTTP e Banco de Dados (`controller/`, `model/`, `repository/`)**: Utilizam anotações do Spring Boot / JPA (`@RestController`, `@Entity`) para simplificar conexões de rede e SQL.

---

## 📂 Mapa de Arquivos e Métodos

### 1. Inicialização e Configuração
- **[`CoreApiApplication.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/CoreApiApplication.java)**:
  - `main(String[] args)`: Inicia o servidor Spring Boot na porta `8080`.
- **[`config/SecurityConfig.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/config/SecurityConfig.java)**:
  - `addCorsMappings(CorsRegistry registry)`: Libera o CORS para o Frontend acessar todas as rotas da API.

### 2. Modelos de Banco de Dados (`model/`)
- **[`User.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/User.java)** (Tabela `perfil_usuario`):
  - Campos: `idUsuario` (`UUID`), `apelido`, `idade`, `peso`, `altura`, `gestanteLactante`, `alergias`, `problemasSaude`, `medicacoesContinuas`, `praticaEsportes`, `horasSono`, `atualizadoEm`.
  - `getImcCalculado()`: Calcula o IMC ($peso / altura^2$) em tempo de execução.
- **[`UserHistory.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/UserHistory.java)** (Tabela `historico_consultas`):
  - Campos: `idConsulta`, `perfilUsuario` (FK `id_usuario` com `ON DELETE CASCADE`), `perguntaUsuario`, `respostaIa`, `dataHora`.
- **[`TrustedSource.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/TrustedSource.java)** (Tabela `trusted_sources`):
  - Armazena links oficiais (ANVISA, Medscape) para o Fallback Seguro.
- **[`Role.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/Role.java)**:
  - Enumeração dos perfis de leitura: `PROFESSIONAL` e `PATIENT`.

### 3. Repositórios JPA (`repository/`)
- **[`UserRepository.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/repository/UserRepository.java)**: CRUD automático por `UUID` na tabela `perfil_usuario`.
- **[`UserHistoryRepository.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/repository/UserHistoryRepository.java)**:
  - `findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(UUID idUsuario)`: Busca o histórico ordenado da consulta mais recente para a mais antiga.

### 4. Serviços de Cálculo em Java Tradicional (`service/`)
- **[`farmCalc.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/service/farmCalc.java)** (100% Java Tradicional — Zero `@`):
  - `totalDose(double weight, double dosePerKg)`: Calcula a dose pediátrica por peso ($mg$).
  - `renalClearanceCalc(int age, double weight, double creatinine, String sex)`: Calcula o Clearance de Creatinina pela fórmula de *Cockcroft-Gault*.
  - `renalFunctionClassification(double renalClearance)`: Classifica o estágio da função renal.

### 5. Controladores REST (`controller/`)
- **[`HealthController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/HealthController.java)**:
  - `GET /api/core/health`: Verifica se o servidor Java está online.
- **[`PerfilController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/PerfilController.java)**:
  - `POST /api/perfil`: Salva ou atualiza (Upsert) o perfil clínico anônimo limpando caracteres `<` e `>`.
  - `GET /api/perfil/{idUsuario}`: Retorna o perfil salvo, o IMC calculado e a lista de histórico.
- **[`CalculatorController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/CalculatorController.java)**:
  - `POST /api/calculators/pediatric`: Aciona `farmCalc.totalDose(...)`.
  - `POST /api/calculators/renal-clearance`: Aciona `farmCalc.renalClearanceCalc(...)` e `farmCalc.renalFunctionClassification(...)`.
- **[`ClinicalController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/ClinicalController.java)**:
  - `POST /api/clinical/analyze`: Encaminha a consulta (`idUsuario` + `question`) para o `ai-engine` Python (`http://localhost:5000/api/ai/query`).
  - `GET /api/clinical/history/{idUsuario}`: Retorna o histórico de consultas daquele `UUID`.
