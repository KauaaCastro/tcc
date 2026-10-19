package com.medinteract.coreapi.service;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;

// Classe utilitária em Java tradicional (sem anotações Spring) para BCrypt e tokens HMAC-SHA256
public class TokenService {

    private static final long EXPIRATION_SECONDS = 86400L;
    private final String secretKey;
    private final BCryptPasswordEncoder bcryptEncoder;

    public TokenService() {
        String envSecret = System.getenv("AUTH_SECRET");
        this.secretKey = (envSecret != null && !envSecret.isBlank())
                ? envSecret
                : "medinteract-tcc-secret-key-2026-hmac-sha256";
        this.bcryptEncoder = new BCryptPasswordEncoder(10);
    }

    public TokenService(String customSecret) {
        this.secretKey = customSecret;
        this.bcryptEncoder = new BCryptPasswordEncoder(10);
    }

    // Gera o hash seguro da senha utilizando BCrypt com salt aleatório (custo 10)
    public String hashPassword(String rawPassword) {
        return bcryptEncoder.encode(rawPassword);
    }

    // Valida a senha contra BCrypt ou legado SHA-256 (sem aceitar texto puro)
    public boolean verifyPassword(String rawPassword, String storedHash) {
        if (rawPassword == null || storedHash == null || storedHash.isBlank()) {
            return false;
        }
        if (storedHash.startsWith("$2a$") || storedHash.startsWith("$2b$") || storedHash.startsWith("$2y$")) {
            return bcryptEncoder.matches(rawPassword, storedHash);
        }
        return sha256Hex(rawPassword).equalsIgnoreCase(storedHash);
    }

    // Indica se o hash armazenado ainda está no formato legado SHA-256 e deve migrar para BCrypt
    public boolean needsRehash(String storedHash) {
        return storedHash == null || !storedHash.startsWith("$2");
    }

    // Emite um token stateless assinado com HMAC-SHA256 contendo UUID do usuário e expiração (24h)
    public String generateToken(UUID userId) {
        long expiresAt = Instant.now().getEpochSecond() + EXPIRATION_SECONDS;
        String payload = userId.toString() + ":" + expiresAt;
        String encodedPayload = Base64.getUrlEncoder().withoutPadding()
                .encodeToString(payload.getBytes(StandardCharsets.UTF_8));
        String signature = signHmac(encodedPayload);
        return encodedPayload + "." + signature;
    }

    // Valida a assinatura HMAC e a expiração do token, retornando o UUID do usuário ou null
    public UUID validateTokenAndGetUserId(String tokenOrHeader) {
        if (tokenOrHeader == null || tokenOrHeader.isBlank()) {
            return null;
        }
        String token = tokenOrHeader.trim();
        if (token.regionMatches(true, 0, "Bearer ", 0, 7)) {
            token = token.substring(7).trim();
        }
        String[] parts = token.split("\\.");
        if (parts.length != 2) {
            return null;
        }
        String expectedSig = signHmac(parts[0]);
        if (!MessageDigest.isEqual(
                expectedSig.getBytes(StandardCharsets.UTF_8),
                parts[1].getBytes(StandardCharsets.UTF_8))) {
            return null;
        }
        try {
            String decoded = new String(Base64.getUrlDecoder().decode(parts[0]), StandardCharsets.UTF_8);
            String[] fields = decoded.split(":");
            if (fields.length != 2) {
                return null;
            }
            long expiresAt = Long.parseLong(fields[1]);
            if (Instant.now().getEpochSecond() > expiresAt) {
                return null;
            }
            return UUID.fromString(fields[0]);
        } catch (Exception e) {
            return null;
        }
    }

    // Calcula a assinatura HMAC-SHA256 em Base64 URL-safe
    private String signHmac(String data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec keySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(keySpec);
            byte[] rawHmac = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(rawHmac);
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao assinar token HMAC-SHA256", e);
        }
    }

    // Calcula hash SHA-256 hexadecimal apenas para compatibilidade e migração de contas legadas
    public String sha256Hex(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hashBytes);
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao calcular SHA-256", e);
        }
    }
}
