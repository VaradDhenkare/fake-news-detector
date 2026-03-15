package com.fakenews.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the Fake News Detector Spring Boot application.
 */
@SpringBootApplication
public class FakeNewsApplication {
    public static void main(String[] args) {
        SpringApplication.run(FakeNewsApplication.class, args);
    }
}
