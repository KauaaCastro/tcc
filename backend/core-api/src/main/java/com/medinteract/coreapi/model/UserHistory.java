package com.medinteract.coreapi.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

import java.time.LocalDateTime;

// Entidade da tabela 'historico_consultas' vinculada ao UUID do perfil anônimo
@Entity
@Table(name = "historico_consultas")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_consulta")
    private Integer idConsulta;

    // Relacionamento com perfil_usuario (apaga o histórico caso o perfil seja removido)
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

    // Preenche a data e hora automaticamente ao registrar a consulta
    @PrePersist
    protected void aoCriar() {
        if (this.dataHora == null) {
            this.dataHora = LocalDateTime.now();
        }
    }
}
