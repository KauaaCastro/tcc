package com.medinteract.coreapi.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.Map;

// Rota de verificação de saúde para checar se o servidor Java está online
@RestController
@RequestMapping("/api/core")
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "medinteract-core-api",
                "version", "1.0.0",
                "timestamp", LocalDateTime.now()
        ));
    }
}
