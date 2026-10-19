package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.FarmHistory;
import com.medinteract.coreapi.model.User;
import com.medinteract.coreapi.model.UserHistory;
import com.medinteract.coreapi.repository.FarmHistoryRepository;
import com.medinteract.coreapi.repository.UserHistoryRepository;
import com.medinteract.coreapi.repository.UserRepository;
import com.medinteract.coreapi.service.TokenService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

// Controlador REST para salvar e buscar a ficha clínica (FarmHistory) e o registro do usuário (UserRegister)
@RestController
@RequestMapping({"/api/perfil", "/perfil"})
public class PerfilController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;
    private final UserHistoryRepository userHistoryRepository;
    // Instanciação tradicional com 'new' seguindo o Padrão Híbrido do projeto
    private final TokenService tokenService = new TokenService();

    public PerfilController(
            UserRepository userRepository,
            FarmHistoryRepository farmHistoryRepository,
            UserHistoryRepository userHistoryRepository
    ) {
        this.userRepository = userRepository;
        this.farmHistoryRepository = farmHistoryRepository;
        this.userHistoryRepository = userHistoryRepository;
    }

    // Salva ou atualiza (Upsert) o usuário em 'user_register' e a ficha clínica em 'farm_history'
    @PostMapping
    public ResponseEntity<Map<String, Object>> salvarOuAtualizarPerfil(
            @RequestBody Map<String, Object> payload,
            @RequestHeader(value = "Authorization", required = false) String authHeader
    ) {
        Object idObj = payload.get("idUsuario") != null ? payload.get("idUsuario") : payload.get("userId");
        UUID idUsuario = parseUuidSeguro(idObj);
        if (idUsuario == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "O campo 'idUsuario' deve ser um UUID v4 válido.",
                    "alert_type", "warning"
            ));
        }

        ResponseEntity<Map<String, Object>> erroAuth = validarAcessoToken(authHeader, idUsuario);
        if (erroAuth != null) {
            return erroAuth;
        }

        String apelido = sanitizarTexto((String) payload.get("apelido"), "Paciente");

        // Preserva email e senha caso o usuário já esteja cadastrado em 'user_register'
        User usuario = userRepository.findById(idUsuario).orElseGet(() -> {
            User novo = new User();
            novo.setIdUsuario(idUsuario);
            return novo;
        });
        usuario.setApelido(apelido);
        userRepository.save(usuario);

        // Monta e salva os dados clínicos na tabela 'farm_history'
        FarmHistory ficha = farmHistoryRepository.findById(idUsuario).orElseGet(() -> new FarmHistory(idUsuario));

        Integer idadeVal = parseInteiroSeguro(payload.get("idade"));
        if (idadeVal != null) {
            ficha.setIdade(idadeVal);
        }
        BigDecimal pesoVal = parseDecimalSeguro(payload.get("peso"));
        if (pesoVal != null) {
            ficha.setPeso(pesoVal);
        }
        BigDecimal alturaVal = parseDecimalSeguro(payload.get("altura"));
        if (alturaVal != null) {
            ficha.setAltura(alturaVal);
        }
        if (payload.get("gestanteLactante") != null) {
            ficha.setGestanteLactante(Boolean.valueOf(payload.get("gestanteLactante").toString()));
        }
        if (payload.containsKey("alergias")) {
            ficha.setAlergias(sanitizarTexto(
                    payload.get("alergias") != null ? payload.get("alergias").toString() : null, null));
        }
        if (payload.containsKey("problemasSaude")) {
            ficha.setProblemasSaude(sanitizarTexto(
                    payload.get("problemasSaude") != null ? payload.get("problemasSaude").toString() : null, null));
        }
        if (payload.containsKey("medicacoesContinuas")) {
            ficha.setMedicacoesContinuas(sanitizarTexto(
                    payload.get("medicacoesContinuas") != null ? payload.get("medicacoesContinuas").toString() : null, null));
        }
        if (payload.containsKey("praticaEsportes")) {
            ficha.setPraticaEsportes(sanitizarTexto(
                    payload.get("praticaEsportes") != null ? payload.get("praticaEsportes").toString() : null, null));
        }
        BigDecimal sonoVal = parseDecimalSeguro(payload.get("horasSono"));
        if (sonoVal != null) {
            ficha.setHorasSono(sonoVal);
        }

        FarmHistory fichaSalva = farmHistoryRepository.save(ficha);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Ficha clínica atualizada com sucesso.");
        resposta.put("usuario", usuario);
        resposta.put("perfil", fichaSalva);
        resposta.put("imcCalculado", fichaSalva.getImcCalculado());

        return ResponseEntity.ok(resposta);
    }

    // Retorna os dados do usuário ('user_register'), ficha clínica ('farm_history') e histórico
    @GetMapping("/{idUsuario}")
    public ResponseEntity<Map<String, Object>> carregarPerfilEHistorico(
            @PathVariable UUID idUsuario,
            @RequestHeader(value = "Authorization", required = false) String authHeader
    ) {
        ResponseEntity<Map<String, Object>> erroAuth = validarAcessoToken(authHeader, idUsuario);
        if (erroAuth != null) {
            return erroAuth;
        }

        Optional<User> optUser = userRepository.findById(idUsuario);
        Optional<FarmHistory> optFicha = farmHistoryRepository.findById(idUsuario);

        if (optUser.isEmpty() && optFicha.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        List<UserHistory> historico = userHistoryRepository
                .findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(idUsuario);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("usuario", optUser.orElse(null));
        resposta.put("perfil", optFicha.orElse(null));
        resposta.put("imcCalculado", optFicha.map(FarmHistory::getImcCalculado).orElse(null));
        resposta.put("historico", historico);

        return ResponseEntity.ok(resposta);
    }

    // Valida a titularidade do token HMAC-SHA256 quando enviado no cabeçalho Authorization
    private ResponseEntity<Map<String, Object>> validarAcessoToken(String authHeader, UUID idUsuarioAlvo) {
        boolean enforceToken = "true".equalsIgnoreCase(System.getenv("ENFORCE_AUTH_TOKEN"));
        if (authHeader == null || authHeader.isBlank()) {
            if (enforceToken) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                        "erro", "Cabeçalho Authorization Bearer é obrigatório.",
                        "alert_type", "restriction"
                ));
            }
            return null;
        }

        UUID tokenUserId = tokenService.validateTokenAndGetUserId(authHeader);
        if (tokenUserId == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Token de autenticação inválido ou expirado.",
                    "alert_type", "restriction"
            ));
        }
        if (!tokenUserId.equals(idUsuarioAlvo)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of(
                    "erro", "Acesso negado: o token informado pertence a outro usuário.",
                    "alert_type", "restriction"
            ));
        }
        return null;
    }

    // Limpa caracteres XML ('<' e '>') das entradas de texto livre
    private String sanitizarTexto(String texto, String valorPadrao) {
        if (texto == null || texto.isBlank()) {
            return valorPadrao;
        }
        return texto.replace("<", "").replace(">", "").trim();
    }

    // Converte UUID de forma segura retornando null caso o formato seja inválido
    private UUID parseUuidSeguro(Object valor) {
        if (valor == null || valor.toString().isBlank()) {
            return null;
        }
        try {
            return UUID.fromString(valor.toString().trim());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    // Converte inteiro de forma segura ignorando strings vazias ou inválidas
    private Integer parseInteiroSeguro(Object valor) {
        if (valor == null || valor.toString().isBlank()) {
            return null;
        }
        try {
            return Integer.valueOf(valor.toString().trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // Converte BigDecimal de forma segura ignorando strings vazias ou inválidas
    private BigDecimal parseDecimalSeguro(Object valor) {
        if (valor == null || valor.toString().isBlank()) {
            return null;
        }
        try {
            return new BigDecimal(valor.toString().trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
