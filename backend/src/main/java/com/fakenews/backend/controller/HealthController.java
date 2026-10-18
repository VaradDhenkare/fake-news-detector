package com.fakenews.backend.controller;

import com.fakenews.backend.service.MlClientService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * HealthController provides an aggregated health check verifying both
 * MySQL 8 database connectivity and Python FastAPI ML microservice status.
 *
 * Endpoint: GET /api/v1/health
 */
@RestController
@RequestMapping("/api/v1")
public class HealthController {

    private final DataSource dataSource;
    private final MlClientService mlClientService;

    public HealthController(DataSource dataSource, MlClientService mlClientService) {
        this.dataSource = dataSource;
        this.mlClientService = mlClientService;
    }

    /**
     * Checks MySQL database connection and ML microservice health.
     *
     * @return 200 OK with system status, or 503 SERVICE UNAVAILABLE if all dependencies down
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getHealth() {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("service", "TruthLens Enterprise Backend");
        response.put("timestamp", Instant.now().toString());

        Map<String, Object> components = new LinkedHashMap<>();

        // 1. MySQL Health Probe
        Map<String, Object> dbStatus = new LinkedHashMap<>();
        boolean dbHealthy = false;
        try (Connection connection = dataSource.getConnection()) {
            if (connection.isValid(2)) {
                dbStatus.put("status", "UP");
                dbStatus.put("database", connection.getMetaData().getDatabaseProductName());
                dbStatus.put("version", connection.getMetaData().getDatabaseProductVersion());
                dbHealthy = true;
            } else {
                dbStatus.put("status", "DOWN");
                dbStatus.put("error", "Database connection validation check failed");
            }
        } catch (Exception e) {
            dbStatus.put("status", "DOWN");
            dbStatus.put("error", e.getMessage() != null ? e.getMessage() : "Failed to obtain DB connection");
        }
        components.put("database", dbStatus);

        // 2. Python FastAPI ML Service Probe
        Map<String, Object> mlStatus = new LinkedHashMap<>();
        boolean mlHealthy = false;
        try {
            Map<String, Object> mlProbe = mlClientService.checkHealth();
            if (mlProbe != null && !"DOWN".equalsIgnoreCase(String.valueOf(mlProbe.get("status")))) {
                mlStatus.put("status", "UP");
                mlStatus.put("details", mlProbe);
                mlHealthy = true;
            } else {
                mlStatus.put("status", "DOWN");
                mlStatus.put("details", mlProbe);
            }
        } catch (Exception e) {
            mlStatus.put("status", "DOWN");
            mlStatus.put("error", e.getMessage());
        }
        components.put("mlService", mlStatus);

        response.put("components", components);

        if (dbHealthy && mlHealthy) {
            response.put("status", "UP");
            return ResponseEntity.ok(response);
        } else if (dbHealthy || mlHealthy) {
            response.put("status", "DEGRADED");
            return ResponseEntity.status(HttpStatus.OK).body(response);
        } else {
            response.put("status", "DOWN");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        }
    }
}
