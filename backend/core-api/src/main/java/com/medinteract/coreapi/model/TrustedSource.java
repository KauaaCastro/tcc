package com.medinteract.coreapi.model;

import jakarta.persistence.*;
import lombok.*;

// Tabela 'trusted_sources': armazena links oficiais (ANVISA/Medscape) para o Fallback Seguro
@Entity
@Table(name = "trusted_sources")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TrustedSource {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private String url;

    @Column(nullable = false)
    private String category;

    @Builder.Default
    @Column(nullable = false)
    private Boolean active = true;
}
