package com.medinteract.coreapi.repository;

import com.medinteract.coreapi.model.UserHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

// Repositório JPA para buscar e salvar registros na tabela 'historico_consultas'
@Repository
public interface UserHistoryRepository extends JpaRepository<UserHistory, Integer> {

    // Busca o histórico de um UUID ordenado da consulta mais recente para a mais antiga
    List<UserHistory> findByPerfilUsuario_IdUsuarioOrderByDataHoraDesc(UUID idUsuario);
}
