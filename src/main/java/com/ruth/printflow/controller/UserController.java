package com.ruth.printflow.controller;

import com.ruth.printflow.dto.UserRegisterRequest;
import com.ruth.printflow.dto.UserResponse;
import com.ruth.printflow.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
public class UserController {

    private final UserService service;

    public UserController(UserService service) {
        this.service = service;
    }

    @PostMapping("/register")
    public ResponseEntity<UserResponse> register(@RequestBody @Valid UserRegisterRequest request) {
        UserResponse savedUser = service.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }
}