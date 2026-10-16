package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.UserHistory;
import com.medinteract.coreapi.repository.UserHistoryRepository;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;

// Conecta o Java ao motor de IA em Python (porta 5000) e consulta o histórico por UUID
@RestController
@RequestMapping("/api/clinical")
public class ClinicalController {

    private final UserHistoryRepository userHistoryRepository;

    @Value("${medinteract.ai-engine.url}")
    private String aiEngineUrl;

    public ClinicalController(UserHistoryRepository userHistoryRepository) {
        this.userHistoryRepository = userHistoryRepository;
    }

    // Envia a pergunta e o idUsuario (UUID) para o Python processar o RAG
    @PostMapping("/analyze")
    public ResponseEntity<Map> analyzeQuery(@RequestBody Map<String, Object> payload) {
        RestClient client = RestClient.create(aiEngineUrl);

        Map aiResponse = client.post()
                .uri("/api/ai/query")
                .body(payload)
                .retrieve()
                .body(Map.class);

        return ResponseEntity.ok(aiResponse);
    }

    // Retorna todas as consultas anteriores vinculadas ao UUID do usuário
    @GetMapping("/history/{idUsuario}")
    public ResponseEntity<List<UserHistory>> getUserHistory(@PathVariable UUID idUsuario) {
        return ResponseEntity.ok(
                userHistoryRepository.findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(idUsuario)
        );
    }
}
