package com.ruth.printflow.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruth.printflow.dto.UserResponse;
import com.ruth.printflow.dto.UserRegisterRequest;
import com.ruth.printflow.service.UserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.doThrow;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(UserController.class)
public class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    public void shouldRegisterUser() throws Exception {
        UserResponse response = new UserResponse(1L, "Copy Print", "copy_print@gmail.com");

        when(userService.register(any(UserRegisterRequest.class))).thenReturn(response);

        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "Senha@123"
        );

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.name").value("Copy Print"))
                .andExpect(jsonPath("$.email").value("copy_print@gmail.com"))
                .andExpect(jsonPath("$.password").doesNotExist());
    }

    @Test
    public void shouldReturnBadRequestWhenNameIsBlank() throws Exception {
        UserRegisterRequest request = new UserRegisterRequest(
                "",
                "copy_print@gmail.com",
                "Senha@123"
        );

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldReturnBadRequestWhenEmailIsInvalid() throws Exception {
        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "email-invalido",
                "Senha@123"
        );

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldReturnBadRequestWhenPasswordIsTooShort() throws Exception {
        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "123"
        );

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldReturnConflictWhenUserAlreadyExists() throws Exception {
        doThrow(new RuntimeException("Já existe um usuário cadastrado"))
                .when(userService)
                .register(any(UserRegisterRequest.class));

        UserRegisterRequest request = new UserRegisterRequest(
                "Copy Print",
                "copy_print@gmail.com",
                "Senha@123"
        );

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").value("Já existe um usuário cadastrado"));
    }
}