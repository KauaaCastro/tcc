package com.medinteract.coreapi.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;

import java.util.UUID;

// Entidade de credenciais de login do usuário (tabela 'user_register')
@Entity
@Table(name = "user_register")
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

    public User() {
    }

    public User(UUID idUsuario, String apelido, String email, String password) {
        this.idUsuario = idUsuario;
        this.apelido = apelido;
        this.email = email;
        this.password = password;
    }

    // Gera automaticamente o UUID v4 caso não seja enviado
    @PrePersist
    protected void aoCriar() {
        if (this.idUsuario == null) {
            this.idUsuario = UUID.randomUUID();
        }
    }

    public UUID getIdUsuario() {
        return idUsuario;
    }

    public void setIdUsuario(UUID idUsuario) {
        this.idUsuario = idUsuario;
    }

    public String getApelido() {
        return apelido;
    }

    public void setApelido(String apelido) {
        this.apelido = apelido;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }
}
