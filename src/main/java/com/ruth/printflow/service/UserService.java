package com.ruth.printflow.service;

import com.ruth.printflow.entity.User;
import com.ruth.printflow.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final UserRepository repository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository repository, PasswordEncoder passwordEncoder) {
        this.repository = repository;
        this.passwordEncoder = passwordEncoder;
    }

    public User register(User user) {
        if (repository.count() > 0) {
            throw new RuntimeException("Já existe um usuário cadastrado");
        }

        String encodedPassword = passwordEncoder.encode(user.getPassword());
        user.setPassword(encodedPassword);

        return repository.save(user);
    }
}