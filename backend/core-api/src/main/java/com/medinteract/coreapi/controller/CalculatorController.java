package com.medinteract.coreapi.controller;

import com.medinteract.coreapi.service.farmCalc;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

// Recebe os dados HTTP do Frontend e aciona a classe tradicional farmCalc
@RestController
@RequestMapping({"/api/calculators", "/api/calculator"})
public class CalculatorController {

    private final farmCalc calculator = new farmCalc();

    // Rota para cálculo de dose pediátrica por peso
    @PostMapping("/pediatric")
    public ResponseEntity<Map<String, Object>> calculatePediatricDose(@RequestBody Map<String, Double> data) {
        double weight = data.getOrDefault("weight", 0.0);
        double dosePerKg = data.getOrDefault("dosePerKg", 0.0);

        double recommendedDose = calculator.totalDose(weight, dosePerKg);

        return ResponseEntity.ok(Map.of(
                "weight", weight,
                "dosePerKg", dosePerKg,
                "recommendedDose", recommendedDose
        ));
    }

    // Rota para cálculo de Clearance de Creatinina (Cockcroft-Gault)
    @PostMapping("/renal-clearance")
    public ResponseEntity<Map<String, Object>> calculateRenalClearance(@RequestBody Map<String, Object> data) {
        int age = ((Number) data.getOrDefault("age", 0)).intValue();
        double weight = ((Number) data.getOrDefault("weight", 0.0)).doubleValue();
        double creatinine = ((Number) data.getOrDefault("creatinine", 1.0)).doubleValue();
        String sex = String.valueOf(data.getOrDefault("sex", "M"));

        double clearance = calculator.renalClearanceCalc(age, weight, creatinine, sex);
        String classification = calculator.renalFunctionClassification(clearance);

        return ResponseEntity.ok(Map.of(
                "renalClearanceMlMin", clearance,
                "renalClassification", classification
        ));
    }
}
