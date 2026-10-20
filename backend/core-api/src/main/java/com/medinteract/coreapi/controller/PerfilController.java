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

// Endpoints para leitura e atualização da ficha clínica do usuário
@RestController
@RequestMapping({"/api/perfil", "/perfil"})
public class PerfilController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;
    private final UserHistoryRepository userHistoryRepository;
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

    @PostMapping
    public ResponseEntity<Map<String, Object>> salvarOuAtualizarPerfil(
            @RequestBody Map<String, Object> payload,
            @RequestHeader(value = "Authorization", required = false) String authHeader
    ) {
        Object idObj = payload.get("idUsuario") != null ? payload.get("idUsuario") : payload.get("userId");
        UUID idUsuario = parseUuid(idObj);
        if (idUsuario == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "ID de usuário inválido.",
                    "alert_type", "warning"
            ));
        }

        ResponseEntity<Map<String, Object>> erroAuth = validarToken(authHeader, idUsuario);
        if (erroAuth != null) {
            return erroAuth;
        }

        Integer idadeVal = parseInteiro(payload.get("idade"));
        BigDecimal pesoVal = parseDecimal(payload.get("peso"));
        BigDecimal alturaVal = parseDecimal(payload.get("altura"));
        BigDecimal sonoVal = parseDecimal(payload.get("horasSono"));

        if ((idadeVal != null && idadeVal < 0)
                || (pesoVal != null && pesoVal.compareTo(BigDecimal.ZERO) <= 0)
                || (alturaVal != null && alturaVal.compareTo(BigDecimal.ZERO) <= 0)
                || (sonoVal != null && sonoVal.compareTo(BigDecimal.ZERO) < 0)) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Os campos numéricos não permitem valores negativos.",
                    "alert_type", "warning"
            ));
        }

        String apelido = limparTexto((String) payload.get("apelido"), "Paciente");

        User usuario = userRepository.findById(idUsuario).orElseGet(() -> {
            User novo = new User();
            novo.setIdUsuario(idUsuario);
            return novo;
        });
        usuario.setApelido(apelido);
        userRepository.save(usuario);

        FarmHistory ficha = farmHistoryRepository.findById(idUsuario).orElseGet(() -> new FarmHistory(idUsuario));

        if (idadeVal != null) ficha.setIdade(idadeVal);
        if (pesoVal != null) ficha.setPeso(pesoVal);
        if (alturaVal != null) ficha.setAltura(alturaVal);
        if (sonoVal != null) ficha.setHorasSono(sonoVal);

        if (payload.get("gestanteLactante") != null) {
            ficha.setGestanteLactante(Boolean.valueOf(payload.get("gestanteLactante").toString()));
        }
        if (payload.containsKey("alergias")) {
            ficha.setAlergias(limparTexto(
                    payload.get("alergias") != null ? payload.get("alergias").toString() : null, null));
        }
        if (payload.containsKey("problemasSaude")) {
            ficha.setProblemasSaude(limparTexto(
                    payload.get("problemasSaude") != null ? payload.get("problemasSaude").toString() : null, null));
        }
        if (payload.containsKey("medicacoesContinuas")) {
            ficha.setMedicacoesContinuas(limparTexto(
                    payload.get("medicacoesContinuas") != null ? payload.get("medicacoesContinuas").toString() : null, null));
        }
        if (payload.containsKey("praticaEsportes")) {
            ficha.setPraticaEsportes(limparTexto(
                    payload.get("praticaEsportes") != null ? payload.get("praticaEsportes").toString() : null, null));
        }

        FarmHistory fichaSalva = farmHistoryRepository.save(ficha);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Ficha clínica atualizada com sucesso.");
        resposta.put("usuario", usuario);
        resposta.put("perfil", fichaSalva);
        resposta.put("imcCalculado", fichaSalva.getImcCalculado());

        return ResponseEntity.ok(resposta);
    }

    @GetMapping("/{idUsuario}")
    public ResponseEntity<Map<String, Object>> carregarPerfilEHistorico(
            @PathVariable UUID idUsuario,
            @RequestHeader(value = "Authorization", required = false) String authHeader
    ) {
        ResponseEntity<Map<String, Object>> erroAuth = validarToken(authHeader, idUsuario);
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

    private ResponseEntity<Map<String, Object>> validarToken(String authHeader, UUID idUsuarioAlvo) {
        boolean enforceToken = "true".equalsIgnoreCase(System.getenv("ENFORCE_AUTH_TOKEN"));
        if (authHeader == null || authHeader.isBlank()) {
            if (enforceToken) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                        "erro", "Cabeçalho Authorization é obrigatório.",
                        "alert_type", "restriction"
                ));
            }
            return null;
        }

        UUID tokenUserId = tokenService.validateTokenAndGetUserId(authHeader);
        if (tokenUserId == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Sessão inválida ou expirada.",
                    "alert_type", "restriction"
            ));
        }
        if (!tokenUserId.equals(idUsuarioAlvo)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of(
                    "erro", "Acesso negado.",
                    "alert_type", "restriction"
            ));
        }
        return null;
    }

    private String limparTexto(String texto, String padrao) {
        if (texto == null || texto.isBlank()) {
            return padrao;
        }
        return texto.replace("<", "").replace(">", "").trim();
    }

    private UUID parseUuid(Object valor) {
        if (valor == null || valor.toString().isBlank()) return null;
        try {
            return UUID.fromString(valor.toString().trim());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    private Integer parseInteiro(Object valor) {
        if (valor == null || valor.toString().isBlank()) return null;
        try {
            return Integer.valueOf(valor.toString().trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private BigDecimal parseDecimal(Object valor) {
        if (valor == null || valor.toString().isBlank()) return null;
        try {
            return new BigDecimal(valor.toString().trim().replace(",", "."));
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
