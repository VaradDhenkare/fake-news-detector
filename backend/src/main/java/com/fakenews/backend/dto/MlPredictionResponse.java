package com.fakenews.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.Map;

/**
 * Maps the JSON response from the Python Flask ML service.
 * ML service returns: { "prediction": "FAKE", "confidence": 0.9432,
 * "probabilities": {...} }
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class MlPredictionResponse {
    private String prediction;
    private Double confidence;
    private Map<String, Double> probabilities;

    public MlPredictionResponse() {
    }

    public String getPrediction() {
        return prediction;
    }

    public void setPrediction(String prediction) {
        this.prediction = prediction;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public Map<String, Double> getProbabilities() {
        return probabilities;
    }

    public void setProbabilities(Map<String, Double> probabilities) {
        this.probabilities = probabilities;
    }
}
