package com.ruth.printflow.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruth.printflow.controller.UserController;
import com.ruth.printflow.entity.User;
import com.ruth.printflow.service.UserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(UserController.class)
@Import(SecurityConfig.class)
public class SecurityConfigTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    public void shouldAllowPublicAccessToRegisterEndpoint() throws Exception {
        User request = new User();
        request.setName("Ruth");
        request.setEmail("ruth@gmail.com");
        request.setPassword("123456");

        User response = new User();
        response.setId(1L);
        response.setName("Ruth");
        response.setEmail("ruth@gmail.com");
        response.setPassword("senha-criptografada");

        when(userService.register(any(User.class))).thenReturn(response);

        mockMvc.perform(post("/users/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated());
    }
}