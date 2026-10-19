package com.medinteract.coreapi;

import com.medinteract.coreapi.model.FarmHistory;
import com.medinteract.coreapi.service.TokenService;
import com.medinteract.coreapi.service.farmCalc;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

// Testes unitários da lógica farmacológica tradicional (farmCalc), IMC e segurança (TokenService)
class CoreApiUnitTest {

    private final farmCalc calculator = new farmCalc();
    private final TokenService tokenService = new TokenService("chave-secreta-teste-unitario-2026");

    // Verifica o cálculo da dose pediátrica total por peso corpóreo
    @Test
    void testPediatricDoseCalculation() {
        double dose = calculator.totalDose(18.5, 15.0);
        assertEquals(277.5, dose, 0.01);
    }

    // Verifica a equação de Cockcroft-Gault para pacientes do sexo masculino e feminino
    @Test
    void testCockcroftGaultClearanceMaleAndFemale() {
        double clearanceMale = calculator.renalClearanceCalc(65, 72.0, 1.2, "M");
        double clearanceFemale = calculator.renalClearanceCalc(65, 72.0, 1.2, "F");
        assertEquals(62.5, clearanceMale, 0.01);
        assertEquals(53.13, clearanceFemale, 0.01);
        assertEquals(0.0, calculator.renalClearanceCalc(65, 72.0, 0.0, "M"));
    }

    // Verifica a classificação clínica dos estágios de função renal
    @Test
    void testRenalFunctionClassification() {
        assertEquals("Normal", calculator.renalFunctionClassification(95.0));
        assertEquals("Leve", calculator.renalFunctionClassification(70.0));
        assertEquals("Moderada", calculator.renalFunctionClassification(45.0));
        assertTrue(calculator.renalFunctionClassification(20.0).contains("severa"));
    }

    // Verifica o cálculo automático de IMC na entidade FarmHistory
    @Test
    void testFarmHistoryImcCalculation() {
        FarmHistory ficha = new FarmHistory(UUID.randomUUID());
        ficha.setPeso(new BigDecimal("81.00"));
        ficha.setAltura(new BigDecimal("1.80"));
        assertEquals(new BigDecimal("25.00"), ficha.getImcCalculado());
    }

    // Verifica o hash BCrypt, a recusa de texto puro e a migração de SHA-256 legado
    @Test
    void testTokenServiceBcryptAndLegacySha256Migration() {
        String raw = "SenhaForte@2026";
        String bcryptHash = tokenService.hashPassword(raw);

        assertTrue(bcryptHash.startsWith("$2a$") || bcryptHash.startsWith("$2b$"));
        assertTrue(tokenService.verifyPassword(raw, bcryptHash));
        assertFalse(tokenService.verifyPassword("SenhaErrada", bcryptHash));
        assertFalse(tokenService.verifyPassword(raw, raw));
        assertFalse(tokenService.needsRehash(bcryptHash));

        String legacySha256 = tokenService.sha256Hex(raw);
        assertTrue(tokenService.verifyPassword(raw, legacySha256));
        assertTrue(tokenService.needsRehash(legacySha256));
    }

    // Verifica a emissão, validação e proteção contra adulteração do token HMAC-SHA256
    @Test
    void testTokenServiceHmacGenerationAndValidation() {
        UUID userId = UUID.randomUUID();
        String token = tokenService.generateToken(userId);

        assertEquals(userId, tokenService.validateTokenAndGetUserId("Bearer " + token));
        assertEquals(userId, tokenService.validateTokenAndGetUserId(token));
        assertNull(tokenService.validateTokenAndGetUserId(token + "adulterado"));
        assertNull(tokenService.validateTokenAndGetUserId("token.invalido"));
    }
}
