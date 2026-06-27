package com.ruth.printflow.service;

import com.ruth.printflow.entity.User;
import com.ruth.printflow.repository.UserRepository;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }

    public User register(User user) {
        if (repository.count()>0){
            throw new RuntimeException("Já existe um usuário cadastrado");
        }
        return repository.save(user);
    }
}