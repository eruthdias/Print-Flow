package com.ruth.printflow.service;

import com.ruth.printflow.entity.User;
import com.ruth.printflow.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

public class UserServiceTest {
    @Test
    public void registerUser() {
        UserRepository repository = Mockito.mock(UserRepository.class);
        when(repository.count()).thenReturn(0L);
        UserService service = new UserService(repository);

        User user = new User();
        user.setName("Ruth");
        user.setEmail("ruth@gmail.com");
        user.setPassword("123456");

        when(repository.save(user)).thenReturn(user);
        User savedUser = service.register(user);
        assertEquals("Ruth", savedUser.getName());
    }
}