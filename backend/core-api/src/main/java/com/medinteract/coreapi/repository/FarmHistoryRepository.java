package com.medinteract.coreapi.repository;

import com.medinteract.coreapi.model.FarmHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

// Repositório JPA para operações de leitura e escrita na tabela 'farm_history'
@Repository
public interface FarmHistoryRepository extends JpaRepository<FarmHistory, UUID> {
}
