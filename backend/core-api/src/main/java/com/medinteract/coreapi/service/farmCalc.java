package com.medinteract.coreapi.service;

public class farmCalc {

    // Calcula a dose pediátrica total (mg) multiplicando o peso (kg) pela dose (mg/kg)
    public double totalDose(double weight, double dosePerKg) {
        double totalDose = weight * dosePerKg;
        return Math.round(totalDose * 100.0) / 100.0;
    }

    // Calcula o Clearance de Creatinina pela fórmula de Cockcroft-Gault
    public double renalClearanceCalc(int age, double weight, double creatinine, String sex) {
        if (creatinine <= 0) {
            return 0.0;
        }

        double renalClearance = ((140.0 - age) * weight) / (72.0 * creatinine);

        if ("F".equalsIgnoreCase(sex)) {
            renalClearance = renalClearance * 0.85;
        }

        return Math.round(renalClearance * 100.0) / 100.0;
    }

    // Classifica o estágio da função renal com base no valor do clearance
    public String renalFunctionClassification(double renalClearance) {
        if (renalClearance >= 90) {
            return "Normal";
        } else if (renalClearance >= 60) {
            return "Leve";
        } else if (renalClearance >= 30) {
            return "Moderada";
        } else {
            return "Regressão renal severa (necessário ajuste rigoroso de dose)";
        }
    }
}