package com.fakenews.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.Map;

/**
 * Maps the JSON response from the Python FastAPI ML service.
 * Supports both legacy ('prediction') and updated ('label') attributes,
 * along with model version, inference latency, and Bruviti ontology mapping.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class MlPredictionResponse {
    private String label;
    private String prediction;
    private Double confidence;
    private String modelVersion;
    private Double inferenceTimeMs;
    private Map<String, Double> probabilities;
    private Map<String, Object> ontologyMapping;

    public MlPredictionResponse() {
    }

    public String getPrediction() {
        return prediction != null ? prediction : label;
    }

    public void setPrediction(String prediction) {
        this.prediction = prediction;
        if (this.label == null) {
            this.label = prediction;
        }
    }

    public String getLabel() {
        return label != null ? label : prediction;
    }

    public void setLabel(String label) {
        this.label = label;
        if (this.prediction == null) {
            this.prediction = label;
        }
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public void setModelVersion(String modelVersion) {
        this.modelVersion = modelVersion;
    }

    public Double getInferenceTimeMs() {
        return inferenceTimeMs;
    }

    public void setInferenceTimeMs(Double inferenceTimeMs) {
        this.inferenceTimeMs = inferenceTimeMs;
    }

    public Map<String, Double> getProbabilities() {
        return probabilities;
    }

    public void setProbabilities(Map<String, Double> probabilities) {
        this.probabilities = probabilities;
    }

    public Map<String, Object> getOntologyMapping() {
        return ontologyMapping;
    }

    public void setOntologyMapping(Map<String, Object> ontologyMapping) {
        this.ontologyMapping = ontologyMapping;
    }
}
