package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.FarmHistory;
import com.medinteract.coreapi.model.User;
import com.medinteract.coreapi.model.UserHistory;
import com.medinteract.coreapi.repository.FarmHistoryRepository;
import com.medinteract.coreapi.repository.UserHistoryRepository;
import com.medinteract.coreapi.repository.UserRepository;
import lombok.RequiredArgsConstructor;
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
@RequiredArgsConstructor
public class PerfilController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;
    private final UserHistoryRepository userHistoryRepository;

    // Salva ou atualiza (Upsert) o usuário em 'user_register' e a ficha clínica em 'farm_history'
    @PostMapping
    public ResponseEntity<Map<String, Object>> salvarOuAtualizarPerfil(@RequestBody Map<String, Object> payload) {
        Object idObj = payload.get("idUsuario") != null ? payload.get("idUsuario") : payload.get("userId");
        if (idObj == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "O campo 'idUsuario' (UUID v4) é obrigatório."
            ));
        }

        UUID idUsuario = UUID.fromString(idObj.toString());
        String apelido = sanitizarTexto((String) payload.get("apelido"), "Paciente");

        // Preserva email e senha caso o usuário já esteja cadastrado em 'user_register'
        User usuario = userRepository.findById(idUsuario).orElseGet(() -> User.builder()
                .idUsuario(idUsuario)
                .build());
        usuario.setApelido(apelido);
        userRepository.save(usuario);

        // Monta e salva os dados clínicos na tabela 'farm_history'
        FarmHistory ficha = farmHistoryRepository.findById(idUsuario).orElseGet(() -> FarmHistory.builder()
                .userId(idUsuario)
                .build());

        if (payload.get("idade") != null) {
            ficha.setIdade(Integer.valueOf(payload.get("idade").toString()));
        }
        if (payload.get("peso") != null) {
            ficha.setPeso(new BigDecimal(payload.get("peso").toString()));
        }
        if (payload.get("altura") != null) {
            ficha.setAltura(new BigDecimal(payload.get("altura").toString()));
        }
        if (payload.get("gestanteLactante") != null) {
            ficha.setGestanteLactante(Boolean.valueOf(payload.get("gestanteLactante").toString()));
        }
        if (payload.containsKey("alergias")) {
            ficha.setAlergias(sanitizarTexto((String) payload.get("alergias"), null));
        }
        if (payload.containsKey("problemasSaude")) {
            ficha.setProblemasSaude(sanitizarTexto((String) payload.get("problemasSaude"), null));
        }
        if (payload.containsKey("medicacoesContinuas")) {
            ficha.setMedicacoesContinuas(sanitizarTexto((String) payload.get("medicacoesContinuas"), null));
        }
        if (payload.containsKey("praticaEsportes")) {
            ficha.setPraticaEsportes(sanitizarTexto((String) payload.get("praticaEsportes"), null));
        }
        if (payload.get("horasSono") != null) {
            ficha.setHorasSono(new BigDecimal(payload.get("horasSono").toString()));
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
    public ResponseEntity<Map<String, Object>> carregarPerfilEHistorico(@PathVariable UUID idUsuario) {
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

    // Limpa caracteres XML ('<' e '>') das entradas de texto livre
    private String sanitizarTexto(String texto, String valorPadrao) {
        if (texto == null || texto.isBlank()) {
            return valorPadrao;
        }
        return texto.replace("<", "").replace(">", "").trim();
    }
}
