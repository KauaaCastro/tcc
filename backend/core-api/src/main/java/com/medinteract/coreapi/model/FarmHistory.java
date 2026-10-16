package com.medinteract.coreapi.model;

import jakarta.persistence.*;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.UUID;

// Entidade da ficha clínica do usuário (tabela 'farm_history') vinculada ao user_register
@Entity
@Table(name = "farm_history")
public class FarmHistory {

    @Id
    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "idade")
    private Integer idade;

    @Column(name = "peso", precision = 5, scale = 2)
    private BigDecimal peso;

    @Column(name = "altura", precision = 3, scale = 2)
    private BigDecimal altura;

    @Column(name = "gestante_lactante")
    private Boolean gestanteLactante = false;

    @Column(name = "alergias", columnDefinition = "TEXT")
    private String alergias;

    @Column(name = "problemas_saude", columnDefinition = "TEXT")
    private String problemasSaude;

    @Column(name = "medicacoes_continuas", columnDefinition = "TEXT")
    private String medicacoesContinuas;

    @Column(name = "pratica_esportes", columnDefinition = "TEXT")
    private String praticaEsportes;

    @Column(name = "horas_sono", precision = 3, scale = 1)
    private BigDecimal horasSono;

    @Column(name = "atualizado_em")
    private LocalDateTime atualizadoEm;

    public FarmHistory() {
    }

    public FarmHistory(UUID userId) {
        this.userId = userId;
        this.gestanteLactante = false;
    }

    // Atualiza a data/hora automaticamente antes de salvar no banco
    @PrePersist
    @PreUpdate
    protected void atualizarDataHora() {
        this.atualizadoEm = LocalDateTime.now();
        if (this.gestanteLactante == null) {
            this.gestanteLactante = false;
        }
    }

    // Calcula o IMC (peso / altura²) em tempo de execução sem criar coluna no banco
    @Transient
    public BigDecimal getImcCalculado() {
        if (peso == null || altura == null || altura.compareTo(BigDecimal.ZERO) <= 0) {
            return null;
        }
        BigDecimal alturaAoQuadrado = altura.multiply(altura);
        return peso.divide(alturaAoQuadrado, 2, RoundingMode.HALF_UP);
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public Integer getIdade() {
        return idade;
    }

    public void setIdade(Integer idade) {
        this.idade = idade;
    }

    public BigDecimal getPeso() {
        return peso;
    }

    public void setPeso(BigDecimal peso) {
        this.peso = peso;
    }

    public BigDecimal getAltura() {
        return altura;
    }

    public void setAltura(BigDecimal altura) {
        this.altura = altura;
    }

    public Boolean getGestanteLactante() {
        return gestanteLactante;
    }

    public void setGestanteLactante(Boolean gestanteLactante) {
        this.gestanteLactante = gestanteLactante;
    }

    public String getAlergias() {
        return alergias;
    }

    public void setAlergias(String alergias) {
        this.alergias = alergias;
    }

    public String getProblemasSaude() {
        return problemasSaude;
    }

    public void setProblemasSaude(String problemasSaude) {
        this.problemasSaude = problemasSaude;
    }

    public String getMedicacoesContinuas() {
        return medicacoesContinuas;
    }

    public void setMedicacoesContinuas(String medicacoesContinuas) {
        this.medicacoesContinuas = medicacoesContinuas;
    }

    public String getPraticaEsportes() {
        return praticaEsportes;
    }

    public void setPraticaEsportes(String praticaEsportes) {
        this.praticaEsportes = praticaEsportes;
    }

    public BigDecimal getHorasSono() {
        return horasSono;
    }

    public void setHorasSono(BigDecimal horasSono) {
        this.horasSono = horasSono;
    }

    public LocalDateTime getAtualizadoEm() {
        return atualizadoEm;
    }

    public void setAtualizadoEm(LocalDateTime atualizadoEm) {
        this.atualizadoEm = atualizadoEm;
    }
}
