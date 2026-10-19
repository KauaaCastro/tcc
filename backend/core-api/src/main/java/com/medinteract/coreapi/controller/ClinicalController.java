package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.UserHistory;
import com.medinteract.coreapi.repository.UserHistoryRepository;
import com.medinteract.coreapi.service.TokenService;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;

// Conecta o Java ao motor de IA em Python (porta 5000) com Fallback Seguro e consulta o histórico por UUID
@RestController
@RequestMapping("/api/clinical")
public class ClinicalController {

    private final UserHistoryRepository userHistoryRepository;
    // Instanciação tradicional com 'new' seguindo o Padrão Híbrido do projeto
    private final TokenService tokenService = new TokenService();

    @Value("${medinteract.ai-engine.url}")
    private String aiEngineUrl;

    public ClinicalController(UserHistoryRepository userHistoryRepository) {
        this.userHistoryRepository = userHistoryRepository;
    }

    // Envia a pergunta ao motor Python e aciona o Fallback Seguro caso a IA esteja indisponível
    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyzeQuery(@RequestBody Map<String, Object> payload) {
        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(Duration.ofSeconds(10));
            factory.setReadTimeout(Duration.ofSeconds(65));

            RestClient client = RestClient.builder()
                    .baseUrl(aiEngineUrl)
                    .requestFactory(factory)
                    .build();

            @SuppressWarnings("unchecked")
            Map<String, Object> aiResponse = client.post()
                    .uri("/api/ai/query")
                    .body(payload)
                    .retrieve()
                    .body(Map.class);

            if (aiResponse != null) {
                return ResponseEntity.ok(aiResponse);
            }
        } catch (Exception e) {
            // Exceção interceptada para retornar contingência segura sem erro 500 bruto
        }

        Map<String, Object> fallback = new LinkedHashMap<>();
        fallback.put("response",
                "[AVISO DE SEGURANÇA CLÍNICA - FALLBACK ATIVADO]\n"
                + "O serviço de Inteligência Artificial está temporariamente indisponível.\n"
                + "Consulte diretamente as fontes oficiais abaixo.");
        fallback.put("sources", List.of());
        fallback.put("severity", "restriction");
        fallback.put("alert_type", "restriction");
        fallback.put("links", List.of(
                Map.of("name", "Bulário Eletrônico da ANVISA", "url", "https://consultas.anvisa.gov.br/#/bulario/"),
                Map.of("name", "Medscape Drug Interaction Checker", "url", "https://reference.medscape.com/drug-interactionchecker")
        ));
        return ResponseEntity.ok(fallback);
    }

    // Retorna todas as consultas anteriores vinculadas ao UUID do usuário validando o token se enviado
    @GetMapping("/history/{idUsuario}")
    public ResponseEntity<?> getUserHistory(
            @PathVariable UUID idUsuario,
            @RequestHeader(value = "Authorization", required = false) String authHeader
    ) {
        if (authHeader != null && !authHeader.isBlank()) {
            UUID tokenUserId = tokenService.validateTokenAndGetUserId(authHeader);
            if (tokenUserId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                        "erro", "Token de autenticação inválido ou expirado.",
                        "alert_type", "restriction"
                ));
            }
            if (!tokenUserId.equals(idUsuario)) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of(
                        "erro", "Acesso negado ao histórico de outro usuário.",
                        "alert_type", "restriction"
                ));
            }
        }
        return ResponseEntity.ok(
                userHistoryRepository.findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(idUsuario)
        );
    }
}
