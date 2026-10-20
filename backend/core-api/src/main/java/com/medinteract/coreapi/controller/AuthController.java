package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.model.FarmHistory;
import com.medinteract.coreapi.model.User;
import com.medinteract.coreapi.repository.FarmHistoryRepository;
import com.medinteract.coreapi.repository.UserRepository;
import com.medinteract.coreapi.service.TokenService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

// Endpoints de cadastro e login de usuário
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;
    private final TokenService tokenService = new TokenService();

    public AuthController(UserRepository userRepository, FarmHistoryRepository farmHistoryRepository) {
        this.userRepository = userRepository;
        this.farmHistoryRepository = farmHistoryRepository;
    }

    private boolean emailValido(String email) {
        if (email == null) return false;
        String limpo = email.trim().toLowerCase();
        int posArroba = limpo.indexOf('@');
        return posArroba > 0 && limpo.contains(".com") && limpo.indexOf(".com") > posArroba + 1;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> cadastrarUsuario(@RequestBody Map<String, String> payload) {
        String email = payload.get("email");
        String password = payload.get("password");
        String apelido = payload.getOrDefault("apelido", payload.getOrDefault("name", "Paciente"));

        if (email == null || email.isBlank() || password == null || password.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Informe email e senha para cadastrar."
            ));
        }

        if (!emailValido(email)) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "O email deve conter '@' e '.com'."
            ));
        }

        if (password.length() < 8) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "A senha deve ter no mínimo 8 caracteres."
            ));
        }

        String emailLimpo = email.trim().toLowerCase();
        if (userRepository.existsByEmail(emailLimpo)) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of(
                    "erro", "Este email já está cadastrado."
            ));
        }

        UUID novoId = UUID.randomUUID();
        User novoUsuario = new User(
                novoId,
                apelido.replace("<", "").replace(">", "").trim(),
                emailLimpo,
                tokenService.hashPassword(password)
        );

        User usuarioSalvo = userRepository.save(novoUsuario);
        FarmHistory fichaSalva = farmHistoryRepository.save(new FarmHistory(novoId));
        String token = tokenService.generateToken(usuarioSalvo.getIdUsuario());

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Usuário cadastrado com sucesso.");
        resposta.put("idUsuario", usuarioSalvo.getIdUsuario());
        resposta.put("token", token);
        resposta.put("usuario", usuarioSalvo);
        resposta.put("perfil", fichaSalva);

        return ResponseEntity.status(HttpStatus.CREATED).body(resposta);
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> autenticarUsuario(@RequestBody Map<String, String> payload) {
        String email = payload.get("email");
        String password = payload.get("password");

        if (email == null || password == null) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Informe email e senha."
            ));
        }

        if (!emailValido(email)) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "O email deve conter '@' e '.com'."
            ));
        }

        if (password.length() < 8) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "A senha deve ter no mínimo 8 caracteres."
            ));
        }

        Optional<User> optUser = userRepository.findByEmail(email.trim().toLowerCase());
        if (optUser.isEmpty()) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Email ou senha inválidos."
            ));
        }

        User usuario = optUser.get();
        if (!tokenService.verifyPassword(password, usuario.getPassword())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Email ou senha inválidos."
            ));
        }

        if (tokenService.needsRehash(usuario.getPassword())) {
            usuario.setPassword(tokenService.hashPassword(password));
            userRepository.save(usuario);
        }

        FarmHistory ficha = farmHistoryRepository.findById(usuario.getIdUsuario()).orElse(null);
        String token = tokenService.generateToken(usuario.getIdUsuario());

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Login realizado com sucesso.");
        resposta.put("idUsuario", usuario.getIdUsuario());
        resposta.put("token", token);
        resposta.put("usuario", usuario);
        resposta.put("perfil", ficha);
        resposta.put("imcCalculado", ficha != null ? ficha.getImcCalculado() : null);

        return ResponseEntity.ok(resposta);
    }
}
