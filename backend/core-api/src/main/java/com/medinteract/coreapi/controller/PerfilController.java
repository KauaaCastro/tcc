package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.User;
import com.medinteract.coreapi.model.UserHistory;
import com.medinteract.coreapi.repository.UserHistoryRepository;
import com.medinteract.coreapi.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

// Controlador REST para salvar e buscar o Perfil Clínico Anônimo e seu histórico por UUID
@RestController
@RequestMapping({"/api/perfil", "/perfil"})
@RequiredArgsConstructor
public class PerfilController {

    private final UserRepository userRepository;
    private final UserHistoryRepository userHistoryRepository;

    // Salva ou atualiza (Upsert) o perfil clínico anônimo no banco
    @PostMapping
    public ResponseEntity<Map<String, Object>> salvarOuAtualizarPerfil(@RequestBody User payload) {
        if (payload.getIdUsuario() == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "O campo 'idUsuario' (UUID v4) é obrigatório."
            ));
        }

        // Remove '<' e '>' dos textos livres para evitar Prompt Injection
        payload.setApelido(sanitizarTexto(payload.getApelido(), "Visitante"));
        payload.setAlergias(sanitizarTexto(payload.getAlergias(), null));
        payload.setProblemasSaude(sanitizarTexto(payload.getProblemasSaude(), null));
        payload.setMedicacoesContinuas(sanitizarTexto(payload.getMedicacoesContinuas(), null));
        payload.setPraticaEsportes(sanitizarTexto(payload.getPraticaEsportes(), null));

        User perfilSalvo = userRepository.save(payload);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Perfil clínico anônimo salvo com sucesso.");
        resposta.put("perfil", perfilSalvo);
        resposta.put("imcCalculado", perfilSalvo.getImcCalculado());

        return ResponseEntity.ok(resposta);
    }

    // Retorna os dados do perfil, o IMC calculado e o histórico de consultas daquele UUID
    @GetMapping("/{idUsuario}")
    public ResponseEntity<Map<String, Object>> carregarPerfilEHistorico(@PathVariable UUID idUsuario) {
        return userRepository.findById(idUsuario)
                .map(perfil -> {
                    List<UserHistory> historico = userHistoryRepository
                            .findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(idUsuario);

                    Map<String, Object> resposta = new LinkedHashMap<>();
                    resposta.put("perfil", perfil);
                    resposta.put("imcCalculado", perfil.getImcCalculado());
                    resposta.put("historico", historico);
                    return ResponseEntity.ok(resposta);
                })
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    // Limpa caracteres XML ('<' e '>') das entradas de texto livre
    private String sanitizarTexto(String texto, String valorPadrao) {
        if (texto == null || texto.isBlank()) {
            return valorPadrao;
        }
        return texto.replace("<", "").replace(">", "").trim();
    }
}
