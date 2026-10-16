package com.medinteract.coreapi.repository;

import com.medinteract.coreapi.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

// Repositório JPA para operações de leitura e escrita na tabela 'perfil_usuario'
@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
}
