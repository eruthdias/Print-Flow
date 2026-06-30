package com.ruth.printflow.service;

import com.ruth.printflow.dto.LoginRequest;
import com.ruth.printflow.dto.LoginResponse;
import com.ruth.printflow.entity.User;
import com.ruth.printflow.exception.InvalidCredentialsException;
import com.ruth.printflow.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserRepository repository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserRepository repository, PasswordEncoder passwordEncoder) {
        this.repository = repository;
        this.passwordEncoder = passwordEncoder;
    }

    public LoginResponse login(LoginRequest request) {
        User user = repository.findByEmail(request.email())
                .orElseThrow(() -> new InvalidCredentialsException("Email ou senha inválidos"));

        boolean passwordMatches = passwordEncoder.matches(
                request.password(),
                user.getPassword()
        );

        if (!passwordMatches) {
            throw new InvalidCredentialsException("Email ou senha inválidos");
        }

        return new LoginResponse(
                "Login realizado com sucesso",
                user.getEmail()
        );
    }
}