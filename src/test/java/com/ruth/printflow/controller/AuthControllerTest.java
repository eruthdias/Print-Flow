package com.ruth.printflow.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruth.printflow.config.SecurityConfig;
import com.ruth.printflow.dto.LoginRequest;
import com.ruth.printflow.dto.LoginResponse;
import com.ruth.printflow.exception.GlobalExceptionHandler;
import com.ruth.printflow.exception.InvalidCredentialsException;
import com.ruth.printflow.service.AuthService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(AuthController.class)
@Import({SecurityConfig.class, GlobalExceptionHandler.class})
public class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AuthService authService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    public void shouldLoginSuccessfully() throws Exception {
        LoginRequest request = new LoginRequest(
                "copy_print@gmail.com",
                "Senha123"
        );

        LoginResponse response = new LoginResponse(
                "Login realizado com sucesso",
                "copy_print@gmail.com"
        );

        when(authService.login(any(LoginRequest.class))).thenReturn(response);

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Login realizado com sucesso"))
                .andExpect(jsonPath("$.email").value("copy_print@gmail.com"));
    }

    @Test
    public void shouldReturnUnauthorizedWhenCredentialsAreInvalid() throws Exception {
        LoginRequest request = new LoginRequest(
                "copy_print@gmail.com",
                "senhaErrada"
        );

        doThrow(new InvalidCredentialsException("Email ou senha inválidos"))
                .when(authService)
                .login(any(LoginRequest.class));

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.message").value("Email ou senha inválidos"));
    }

    @Test
    public void shouldReturnBadRequestWhenEmailIsBlank() throws Exception {
        LoginRequest request = new LoginRequest(
                "",
                "Senha123"
        );

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldReturnBadRequestWhenEmailIsInvalid() throws Exception {
        LoginRequest request = new LoginRequest(
                "email-invalido",
                "Senha123"
        );

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldReturnBadRequestWhenPasswordIsBlank() throws Exception {
        LoginRequest request = new LoginRequest(
                "copy_print@gmail.com",
                ""
        );

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}