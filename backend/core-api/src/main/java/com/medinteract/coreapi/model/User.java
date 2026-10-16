package com.medinteract.coreapi.model;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.UUID;

// Entidade do Perfil Clínico Anônimo (tabela 'perfil_usuario') identificada via UUID v4
@Entity
@Table(name = "perfil_usuario")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    // UUID v4 gerado no navegador (localStorage)
    @Id
    @Column(name = "id_usuario", nullable = false, updatable = false)
    private UUID idUsuario;

    @Column(name = "apelido", length = 50, nullable = false)
    private String apelido;

    @Column(name = "idade")
    private Integer idade;

    @Column(name = "peso", precision = 5, scale = 2)
    private BigDecimal peso;

    @Column(name = "altura", precision = 3, scale = 2)
    private BigDecimal altura;

    @Builder.Default
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
}
