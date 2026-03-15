package com.fakenews.backend.exception;

/**
 * Thrown when a resource (User, NewsAnalysis) is not found.
 * Maps to HTTP 404 via GlobalExceptionHandler.
 */
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
