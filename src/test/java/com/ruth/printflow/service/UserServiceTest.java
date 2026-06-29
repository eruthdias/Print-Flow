package com.ruth.printflow.service;

import com.ruth.printflow.dto.UserRegisterRequest;
import com.ruth.printflow.dto.UserResponse;
import com.ruth.printflow.entity.User;
import com.ruth.printflow.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

public class UserServiceTest {

    @Test
    public void shouldRegisterUserWhenThereIsNoUserYet() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        when(repository.count()).thenReturn(0L);
        when(passwordEncoder.encode("Senha@123")).thenReturn("senha-criptografada");

        when(repository.save(Mockito.any(User.class))).thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(1L);
            return user;
        });

        UserService service = new UserService(repository, passwordEncoder);

        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "Senha@123"
        );

        UserResponse response = service.register(request);

        assertEquals(1L, response.id());
        assertEquals("Copy Print", response.name());
        assertEquals("copy_print@gmail.com", response.email());
    }

    @Test
    public void shouldNotRegisterUserWhenUserAlreadyExists() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        when(repository.count()).thenReturn(1L);

        UserService service = new UserService(repository, passwordEncoder);

        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "Senha@123"
        );

        RuntimeException exception = assertThrows(
                RuntimeException.class,
                () -> service.register(request)
        );

        assertEquals("Já existe um usuário cadastrado", exception.getMessage());
    }

    @Test
    public void shouldEncodePasswordWhenRegisteringUser() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        PasswordEncoder passwordEncoder = Mockito.mock(PasswordEncoder.class);

        when(repository.count()).thenReturn(0L);
        when(passwordEncoder.encode("Senha@123")).thenReturn("senha-criptografada");

        when(repository.save(Mockito.any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        UserService service = new UserService(repository, passwordEncoder);

        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "Senha@123"
        );

        service.register(request);

        Mockito.verify(passwordEncoder).encode("Senha@123");
        Mockito.verify(repository).save(Mockito.argThat(user ->
                user.getPassword().equals("senha-criptografada")
        ));
    }
}