package com.fakenews.backend.exception;

/**
 * Thrown when registration fields conflict (duplicate username/email).
 * Maps to HTTP 409 via GlobalExceptionHandler.
 */
public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
