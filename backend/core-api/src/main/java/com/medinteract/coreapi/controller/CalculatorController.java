package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.service.farmCalc;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

// Recebe os dados HTTP do Frontend e aciona a classe tradicional farmCalc
@RestController
@RequestMapping({"/api/calculators", "/api/calculator"})
public class CalculatorController {

    private final farmCalc calculator = new farmCalc();

    // Rota para cálculo de dose pediátrica por peso (suporta /pediatric e /pediatric-dose)
    @PostMapping({"/pediatric", "/pediatric-dose"})
    public ResponseEntity<Map<String, Object>> calculatePediatricDose(@RequestBody Map<String, Object> data) {
        double weight = parseDoubleSeguro(data.get("weight"), 0.0);
        double dosePerKg = parseDoubleSeguro(data.get("dosePerKg"), 0.0);

        if (weight <= 0 || dosePerKg <= 0) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Peso e dose por kg devem ser maiores que zero.",
                    "alert_type", "warning"
            ));
        }

        double recommendedDose = calculator.totalDose(weight, dosePerKg);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("weight", weight);
        resposta.put("dosePerKg", dosePerKg);
        resposta.put("recommendedDose", recommendedDose);
        resposta.put("totalDoseMg", recommendedDose);
        resposta.put("unit", "mg");
        return ResponseEntity.ok(resposta);
    }

    // Rota para cálculo de Clearance de Creatinina (Cockcroft-Gault)
    @PostMapping("/renal-clearance")
    public ResponseEntity<Map<String, Object>> calculateRenalClearance(@RequestBody Map<String, Object> data) {
        int age = (int) parseDoubleSeguro(data.get("age"), 0.0);
        double weight = parseDoubleSeguro(data.get("weight"), 0.0);
        double creatinine = parseDoubleSeguro(data.get("creatinine"), 0.0);
        String sex = String.valueOf(data.getOrDefault("sex", "M"));

        if (age <= 0 || weight <= 0 || creatinine <= 0) {
            return ResponseEntity.badRequest().body(Map.of(
                    "erro", "Idade, peso e creatinina sérica devem ser maiores que zero.",
                    "alert_type", "warning"
            ));
        }

        double clearance = calculator.renalClearanceCalc(age, weight, creatinine, sex);
        String classification = calculator.renalFunctionClassification(clearance);

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("renalClearanceMlMin", clearance);
        resposta.put("creatinineClearance", clearance);
        resposta.put("unit", "mL/min");
        resposta.put("renalClassification", classification);
        resposta.put("renalStageClassification", classification);
        return ResponseEntity.ok(resposta);
    }

    // Converte valores numéricos de forma segura evitando NumberFormatException
    private double parseDoubleSeguro(Object valor, double padrao) {
        if (valor == null) {
            return padrao;
        }
        try {
            return Double.parseDouble(valor.toString().trim());
        } catch (NumberFormatException e) {
            return padrao;
        }
    }
}
