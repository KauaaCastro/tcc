package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.FarmHistory;
import com.medinteract.coreapi.model.User;
import com.medinteract.coreapi.repository.FarmHistoryRepository;
import com.medinteract.coreapi.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

// Controlador REST para cadastro e login de usuários na tabela 'user_register'
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;

    // Cadastra um novo usuário em 'user_register' e inicializa sua ficha em 'farm_history'
    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> cadastrarUsuario(@RequestBody Map<String, String> payload) {
        String email = payload.get("email");
        String password = payload.get("password");
        String apelido = payload.getOrDefault("apelido", payload.getOrDefault("name", "Paciente"));

        if (email == null || email.isBlank() || password == null || password.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Email e senha são obrigatórios para o cadastro."
            ));
        }

        String emailLimpo = email.trim().toLowerCase();
        if (userRepository.existsByEmail(emailLimpo)) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of(
                    "erro", "Este email já está cadastrado."
            ));
        }

        UUID novoId = UUID.randomUUID();
        User novoUsuario = User.builder()
                .idUsuario(novoId)
                .apelido(apelido.replace("<", "").replace(">", "").trim())
                .email(emailLimpo)
                .password(gerarHashSenha(password))
                .build();

        User usuarioSalvo = userRepository.save(novoUsuario);

        FarmHistory fichaInicial = FarmHistory.builder()
                .userId(novoId)
                .gestanteLactante(false)
                .build();
        FarmHistory fichaSalva = farmHistoryRepository.save(fichaInicial);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Usuário cadastrado com sucesso.");
        resposta.put("idUsuario", usuarioSalvo.getIdUsuario());
        resposta.put("usuario", usuarioSalvo);
        resposta.put("perfil", fichaSalva);

        return ResponseEntity.status(HttpStatus.CREATED).body(resposta);
    }

    // Autentica o usuário validando email e senha e retorna seu UUID e ficha clínica
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> autenticarUsuario(@RequestBody Map<String, String> payload) {
        String email = payload.get("email");
        String password = payload.get("password");

        if (email == null || password == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Informe email e senha."
            ));
        }

        Optional<User> optUser = userRepository.findByEmail(email.trim().toLowerCase());
        if (optUser.isEmpty()) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Email ou senha inválidos."
            ));
        }

        User usuario = optUser.get();
        String hashInformado = gerarHashSenha(password);

        // Aceita tanto senha com hash SHA-256 quanto texto simples (caso inserido manualmente no banco)
        boolean senhaValida = hashInformado.equals(usuario.getPassword()) || password.equals(usuario.getPassword());
        if (!senhaValida) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Email ou senha inválidos."
            ));
        }

        FarmHistory ficha = farmHistoryRepository.findById(usuario.getIdUsuario()).orElse(null);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Login realizado com sucesso.");
        resposta.put("idUsuario", usuario.getIdUsuario());
        resposta.put("usuario", usuario);
        resposta.put("perfil", ficha);
        resposta.put("imcCalculado", ficha != null ? ficha.getImcCalculado() : null);

        return ResponseEntity.ok(resposta);
    }

    // Gera hash SHA-256 da senha usando biblioteca padrão do Java
    private String gerarHashSenha(String senha) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(senha.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hashBytes);
        } catch (Exception e) {
            return senha;
        }
    }
}
