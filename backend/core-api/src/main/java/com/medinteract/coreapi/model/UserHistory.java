package com.medinteract.coreapi.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

import java.time.LocalDateTime;

// Entidade da tabela 'historico_consultas' vinculada ao UUID do usuário
@Entity
@Table(name = "historico_consultas")
public class UserHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_consulta")
    private Integer idConsulta;

    // Relacionamento com user_register (apaga o histórico caso o usuário seja removido)
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_usuario", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @JsonIgnore
    private User perfilUsuario;

    @Column(name = "pergunta_usuario", columnDefinition = "TEXT", nullable = false)
    private String perguntaUsuario;

    @Column(name = "resposta_ia", columnDefinition = "TEXT", nullable = false)
    private String respostaIa;

    @Column(name = "data_hora")
    private LocalDateTime dataHora;

    public UserHistory() {
    }

    // Preenche a data e hora automaticamente ao registrar a consulta
    @PrePersist
    protected void aoCriar() {
        if (this.dataHora == null) {
            this.dataHora = LocalDateTime.now();
        }
    }

    public Integer getIdConsulta() {
        return idConsulta;
    }

    public void setIdConsulta(Integer idConsulta) {
        this.idConsulta = idConsulta;
    }

    public User getPerfilUsuario() {
        return perfilUsuario;
    }

    public void setPerfilUsuario(User perfilUsuario) {
        this.perfilUsuario = perfilUsuario;
    }

    public String getPerguntaUsuario() {
        return perguntaUsuario;
    }

    public void setPerguntaUsuario(String perguntaUsuario) {
        this.perguntaUsuario = perguntaUsuario;
    }

    public String getRespostaIa() {
        return respostaIa;
    }

    public void setRespostaIa(String respostaIa) {
        this.respostaIa = respostaIa;
    }

    public LocalDateTime getDataHora() {
        return dataHora;
    }

    public void setDataHora(LocalDateTime dataHora) {
        this.dataHora = dataHora;
    }
}
