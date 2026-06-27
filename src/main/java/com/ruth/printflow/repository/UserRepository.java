package com.ruth.printflow.repository;

import com.ruth.printflow.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {

}