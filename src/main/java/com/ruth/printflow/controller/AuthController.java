package com.ruth.printflow.controller;

import com.ruth.printflow.dto.LoginRequest;
import com.ruth.printflow.dto.LoginResponse;
import com.ruth.printflow.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService service;

    public AuthController(AuthService service) {
        this.service = service;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody @Valid LoginRequest request) {
        LoginResponse response = service.login(request);
        return ResponseEntity.ok(response);
    }
}