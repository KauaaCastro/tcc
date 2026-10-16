# ☕ MedInteract Core API (Java 17 / Spring Boot 3)

Backend Java responsável pelo gerenciamento de **Autenticação (`user_register`)**, **Ficha Clínica (`farm_history`)**, **Histórico de Consultas**, **Calculadoras Farmacêuticas Determinísticas** e **Orquestração com o Motor de IA (`ai-engine`)**.

---

## 🏛️ Padrão Arquitetural Adotado

1. **Separação entre Login (`user_register`) e Ficha Clínica (`farm_history`)**:
   - Credenciais de acesso (`id_usuario` UUID, `apelido`, `email`, `password` com hash SHA-256) ficam isoladas na tabela `user_register`.
   - Dados clínicos e estilo de vida ficam vinculados na tabela `farm_history` (`user_id` UUID).
2. **Arquitetura Híbrida (Java Tradicional + Anotações de Conexão)**:
   - **Regras de Negócio e Cálculos (`service/`)**: Escritos em **Java 100% Tradicional** (classes comuns sem `@`, instanciadas com `new`, sem dependência de Lombok).
   - **Conexões HTTP e Banco de Dados (`controller/`, `model/`, `repository/`)**: Utilizam anotações do Spring Boot / JPA (`@RestController`, `@Entity`) para simplificar conexões de rede e SQL.

---

## 🛠️ Comandos Rápidos de Verificação e Build (`npm run`)

A partir da raiz do repositório (`C:\workspace\tcc`), execute:

```bash
# Compila e verifica erros em todas as classes Java (Maven test-compile)
npm run check:java

# Verifica simultaneamente Python (ai-engine) + Java (core-api)
npm run check

# Gera o pacote .jar da Core API Java
npm run build:java
```

---

## 📂 Mapa de Arquivos e Métodos

### 1. Inicialização e Configuração
- **[`CoreApiApplication.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/CoreApiApplication.java)**:
  - `main(String[] args)`: Inicia o servidor Spring Boot na porta `8080`.
- **[`config/SecurityConfig.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/config/SecurityConfig.java)**:
  - `addCorsMappings(CorsRegistry registry)`: Libera o CORS para o Frontend acessar todas as rotas da API.

### 2. Modelos de Banco de Dados (`model/`)
- **[`User.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/User.java)** (Tabela `user_register`):
  - Campos: `idUsuario` (`UUID`), `apelido`, `email`, `password` (`WRITE_ONLY`).
- **[`FarmHistory.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/FarmHistory.java)** (Tabela `farm_history`):
  - Campos: `userId` (`UUID`), `idade`, `peso`, `altura`, `gestanteLactante`, `alergias`, `problemasSaude`, `medicacoesContinuas`, `praticaEsportes`, `horasSono`, `atualizadoEm`.
  - `getImcCalculado()`: Calcula o IMC ($peso / altura^2$) em tempo de execução.
- **[`UserHistory.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/UserHistory.java)** (Tabela `historico_consultas`):
  - Campos: `idConsulta`, `perfilUsuario` (FK `id_usuario` com `ON DELETE CASCADE`), `perguntaUsuario`, `respostaIa`, `dataHora`.
- **[`TrustedSource.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/TrustedSource.java)** (Tabela `trusted_sources`):
  - Armazena links oficiais (ANVISA, Medscape) para o Fallback Seguro.
- **[`Role.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/model/Role.java)**:
  - Enumeração dos perfis de leitura: `PROFESSIONAL` e `PATIENT`.

### 3. Repositórios JPA (`repository/`)
- **[`UserRepository.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/repository/UserRepository.java)**: CRUD por `UUID` e busca por `email` (`findByEmail`, `existsByEmail`) na tabela `user_register`.
- **[`FarmHistoryRepository.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/repository/FarmHistoryRepository.java)**: CRUD por `UUID` na tabela `farm_history`.
- **[`UserHistoryRepository.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/repository/UserHistoryRepository.java)**:
  - `findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(UUID idUsuario)`: Busca o histórico ordenado da consulta mais recente para a mais antiga.

### 4. Serviços de Cálculo em Java Tradicional (`service/`)
- **[`farmCalc.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/service/farmCalc.java)** (100% Java Tradicional — Zero `@`):
  - `totalDose(double weight, double dosePerKg)`: Calcula a dose pediátrica por peso ($mg$).
  - `renalClearanceCalc(int age, double weight, double creatinine, String sex)`: Calcula o Clearance de Creatinina pela fórmula de *Cockcroft-Gault*.
  - `renalFunctionClassification(double renalClearance)`: Classifica o estágio da função renal.

### 5. Controladores REST (`controller/`)
- **[`AuthController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/AuthController.java)**:
  - `POST /api/auth/register`: Cadastra novo usuário em `user_register` (com hash `SHA-256`) e inicializa sua ficha em `farm_history`.
  - `POST /api/auth/login`: Autentica por `email` e `password` e retorna `idUsuario`, dados do usuário, ficha clínica e IMC.
- **[`PerfilController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/PerfilController.java)**:
  - `POST /api/perfil`: Salva ou atualiza (Upsert) a ficha clínica (`farm_history`) e o apelido (`user_register`) limpando caracteres `<` e `>`.
  - `GET /api/perfil/{idUsuario}`: Retorna os dados do usuário, ficha clínica, IMC calculado e a lista de histórico.
- **[`CalculatorController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/CalculatorController.java)**:
  - `POST /api/calculators/pediatric`: Aciona `farmCalc.totalDose(...)`.
  - `POST /api/calculators/renal-clearance`: Aciona `farmCalc.renalClearanceCalc(...)` e `farmCalc.renalFunctionClassification(...)`.
- **[`ClinicalController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/ClinicalController.java)**:
  - `POST /api/clinical/analyze`: Encaminha a consulta (`idUsuario` + `question`) para o `ai-engine` Python (`http://localhost:5000/api/ai/query`).
  - `GET /api/clinical/history/{idUsuario}`: Retorna o histórico de consultas daquele `UUID`.
- **[`HealthController.java`](file:///C:/workspace/tcc/backend/core-api/src/main/java/com/medinteract/coreapi/controller/HealthController.java)**:
  - `GET /api/core/health`: Verifica se o servidor Java está online.
