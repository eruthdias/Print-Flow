package com.ruth.printflow.controller;

import com.ruth.printflow.entity.User;
import com.ruth.printflow.service.UserService;
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
    public ResponseEntity<User> register(@RequestBody User user) {
        User savedUser = service.register(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }
}