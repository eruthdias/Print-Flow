package com.ruth.printflow.service;

import com.ruth.printflow.dto.LoginRequest;
import com.ruth.printflow.dto
        .LoginResponse;
import com.ruth.printflow.entity.User;
import com.ruth.printflow.exception.InvalidCredentialsException;
import com.ruth.printflow.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

public class AuthServiceTest {

    @Test
    public void shouldLoginWithValidCredentials() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        User user = new User();
        user.setId(1L);
        user.setName("Copy Print");
        user.setEmail("copy_print@gmail.com");
        user.setPassword("senha-criptografada");

        when(repository.findByEmail("copy_print@gmail.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("Senha123", "senha-criptografada")).thenReturn(true);

        AuthService service = new AuthService(repository, passwordEncoder);

        LoginRequest request = new LoginRequest("copy_print@gmail.com", "Senha123");

        LoginResponse response = service.login(request);

        assertEquals("Login realizado com sucesso", response.message());
        assertEquals("copy_print@gmail.com", response.email());
    }

    @Test
    public void shouldNotLoginWhenEmailDoesNotExist() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        when(repository.findByEmail("errado@gmail.com")).thenReturn(Optional.empty());

        AuthService service = new AuthService(repository, passwordEncoder);

        LoginRequest request = new LoginRequest("errado@gmail.com", "Senha123");

        assertThrows(InvalidCredentialsException.class, () -> service.login(request));
    }

    @Test
    public void shouldNotLoginWhenPasswordIsInvalid() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        User user = new User();
        user.setEmail("copy_print@gmail.com");
        user.setPassword("senha-criptografada");

        when(repository.findByEmail("copy_print@gmail.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("senhaErrada", "senha-criptografada")).thenReturn(false);

        AuthService service = new AuthService(repository, passwordEncoder);

        LoginRequest request = new LoginRequest("copy_print@gmail.com", "senhaErrada");

        assertThrows(InvalidCredentialsException.class, () -> service.login(request));
    }
}