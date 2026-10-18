package com.fakenews.backend.service;

import com.fakenews.backend.dto.LiveFeedResponse;
import com.fakenews.backend.dto.MlPredictionResponse;
import com.fakenews.backend.dto.MlUrlPredictionResponse;
import com.fakenews.backend.exception.MlServiceException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

/**
 * Reactive WebClient service for communicating with the Python FastAPI ML microservice.
 * Supports configurable URL, robust timeout resilience, and health probe diagnostics.
 */
@Service
public class MlClientService {

    private static final Logger log = LoggerFactory.getLogger(MlClientService.class);

    private final WebClient webClient;
    private final Duration timeout;
    private final String predictPath;
    private final String predictUrlPath;
    private final String liveFeedPath;
    private final String baseUrl;

    public MlClientService(
            WebClient.Builder webClientBuilder,
            @Value("${ml.service.url:${ml.service.base-url:http://localhost:5001}}") String baseUrl,
            @Value("${ml.service.predict-path:/predict}") String predictPath,
            @Value("${ml.service.predict-url-path:/predict-url}") String predictUrlPath,
            @Value("${ml.service.live-feed-path:/live-feed}") String liveFeedPath,
            @Value("${ml.service.timeout-seconds:10}") long timeoutSeconds) {
        this.baseUrl = baseUrl;
        this.webClient = webClientBuilder.baseUrl(baseUrl).build();
        this.predictPath = predictPath;
        this.predictUrlPath = predictUrlPath;
        this.liveFeedPath = liveFeedPath;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
        log.info("Initialized MlClientService with endpoint URL: {}", baseUrl);
    }

    /**
     * Checks the health and readiness of the ML microservice.
     *
     * @return Map containing health metadata from FastAPI /health
     */
    public Map<String, Object> checkHealth() {
        try {
            return webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(4))
                    .block();
        } catch (Exception e) {
            log.warn("Health probe failed for ML service at {}: {}", baseUrl, e.getMessage());
            return Map.of(
                    "status", "DOWN",
                    "error", e.getMessage() != null ? e.getMessage() : "Connection failed",
                    "url", baseUrl
            );
        }
    }

    /**
     * Sends news text to FastAPI /predict endpoint.
     *
     * @param newsText raw text content
     * @return predicted veracity and confidence metadata
     */
    public MlPredictionResponse predict(String newsText) {
        log.debug("Calling ML service POST {}", predictPath);
        try {
            MlPredictionResponse response = webClient.post()
                    .uri(predictPath)
                    .bodyValue(Map.of("text", newsText, "newsText", newsText))
                    .retrieve()
                    .onStatus(
                            status -> status.is4xxClientError() || status.is5xxServerError(),
                            res -> res.bodyToMono(String.class)
                                    .flatMap(body -> Mono.error(
                                            new MlServiceException("ML service error: " + body))))
                    .bodyToMono(MlPredictionResponse.class)
                    .timeout(timeout)
                    .block();
            if (response == null) {
                throw new MlServiceException("ML service returned an empty response.");
            }
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service at " + baseUrl + ". Is it running?", e);
        }
    }

    /**
     * Sends article URL to FastAPI /predict-url endpoint.
     *
     * @param url article URL
     * @return extracted text analysis and prediction
     */
    public MlUrlPredictionResponse predictUrl(String url) {
        log.debug("Calling ML service POST {} for URL: {}", predictUrlPath, url);
        try {
            Duration urlTimeout = Duration.ofSeconds(Math.max(timeout.toSeconds(), 30));
            MlUrlPredictionResponse response = webClient.post()
                    .uri(predictUrlPath)
                    .bodyValue(Map.of("url", url))
                    .retrieve()
                    .onStatus(
                            status -> status.is4xxClientError() || status.is5xxServerError(),
                            res -> res.bodyToMono(String.class)
                                    .flatMap(body -> Mono.error(
                                            new MlServiceException("ML url-predict error: " + body))))
                    .bodyToMono(MlUrlPredictionResponse.class)
                    .timeout(urlTimeout)
                    .block();
            if (response == null) {
                throw new MlServiceException("ML service returned an empty response for URL prediction.");
            }
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service at " + baseUrl + ". Is it running?", e);
        }
    }

    /**
     * Fetches live RSS news headlines and classification results.
     *
     * @param maxPerSource max articles per RSS provider
     * @return aggregated live feed results
     */
    public LiveFeedResponse getLiveFeed(int maxPerSource) {
        log.debug("Calling ML service GET {}?max_per_source={}", liveFeedPath, maxPerSource);
        try {
            Duration feedTimeout = Duration.ofSeconds(60);
            LiveFeedResponse response = webClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path(liveFeedPath)
                            .queryParam("max_per_source", maxPerSource)
                            .build())
                    .retrieve()
                    .onStatus(
                            status -> status.is4xxClientError() || status.is5xxServerError(),
                            res -> res.bodyToMono(String.class)
                                    .flatMap(body -> Mono.error(
                                            new MlServiceException("ML live-feed error: " + body))))
                    .bodyToMono(LiveFeedResponse.class)
                    .timeout(feedTimeout)
                    .block();
            if (response == null) {
                throw new MlServiceException("ML service returned an empty live-feed response.");
            }
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service at " + baseUrl + " for live feed.", e);
        }
    }
}
