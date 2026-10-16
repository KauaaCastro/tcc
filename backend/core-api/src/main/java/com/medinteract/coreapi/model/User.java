package com.medinteract.coreapi.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

// Entidade de credenciais de login do usuário (tabela 'user_register')
@Entity
@Table(name = "user_register")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    @Id
    @Column(name = "id_usuario", nullable = false, updatable = false)
    private UUID idUsuario;

    @Column(name = "apelido", length = 50, nullable = false)
    private String apelido;

    @Column(name = "email", length = 100, unique = true)
    private String email;

    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    @Column(name = "password", length = 255)
    private String password;

    // Gera automaticamente o UUID v4 caso não seja enviado
    @PrePersist
    protected void aoCriar() {
        if (this.idUsuario == null) {
            this.idUsuario = UUID.randomUUID();
        }
    }
}
