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

// Controlador REST para cadastro e login de usuários na tabela 'user_register'
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final FarmHistoryRepository farmHistoryRepository;
    // Instanciação tradicional com 'new' seguindo o Padrão Híbrido do projeto
    private final TokenService tokenService = new TokenService();

    public AuthController(UserRepository userRepository, FarmHistoryRepository farmHistoryRepository) {
        this.userRepository = userRepository;
        this.farmHistoryRepository = farmHistoryRepository;
    }

    // Cadastra um novo usuário em 'user_register' com BCrypt e inicializa sua ficha em 'farm_history'
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
        User novoUsuario = new User(
                novoId,
                apelido.replace("<", "").replace(">", "").trim(),
                emailLimpo,
                tokenService.hashPassword(password)
        );

        User usuarioSalvo = userRepository.save(novoUsuario);

        FarmHistory fichaInicial = new FarmHistory(novoId);
        FarmHistory fichaSalva = farmHistoryRepository.save(fichaInicial);
        String token = tokenService.generateToken(usuarioSalvo.getIdUsuario());

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("mensagem", "Usuário cadastrado com sucesso.");
        resposta.put("idUsuario", usuarioSalvo.getIdUsuario());
        resposta.put("token", token);
        resposta.put("usuario", usuarioSalvo);
        resposta.put("perfil", fichaSalva);

        return ResponseEntity.status(HttpStatus.CREATED).body(resposta);
    }

    // Autentica o usuário validando email e senha (BCrypt) e retorna seu UUID, token HMAC e ficha clínica
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
        if (!tokenService.verifyPassword(password, usuario.getPassword())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of(
                    "erro", "Email ou senha inválidos."
            ));
        }

        // Migra transparentemente hashes legados SHA-256 para BCrypt no primeiro login válido
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
