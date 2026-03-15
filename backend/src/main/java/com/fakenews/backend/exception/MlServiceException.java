package com.fakenews.backend.exception;

/**
 * Thrown when the ML service is unreachable or returns an unexpected error.
 * Maps to HTTP 502 via GlobalExceptionHandler.
 */
public class MlServiceException extends RuntimeException {
    public MlServiceException(String message, Throwable cause) {
        super(message, cause);
    }
    public MlServiceException(String message) {
        super(message);
    }
}
