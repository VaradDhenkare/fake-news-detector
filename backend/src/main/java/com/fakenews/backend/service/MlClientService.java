package com.fakenews.backend.service;

import com.fakenews.backend.dto.LiveFeedResponse;
import com.fakenews.backend.dto.MlPredictionResponse;
import com.fakenews.backend.dto.MlUrlPredictionResponse;
import com.fakenews.backend.exception.MlServiceException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

@Service
public class MlClientService {

    private static final Logger log = LoggerFactory.getLogger(MlClientService.class);

    private final WebClient webClient;
    private final Duration timeout;
    private final String predictPath;
    private final String predictUrlPath;
    private final String liveFeedPath;

    public MlClientService(
            WebClient.Builder webClientBuilder,
            @Value("${ml.service.base-url}") String baseUrl,
            @Value("${ml.service.predict-path}") String predictPath,
            @Value("${ml.service.predict-url-path}") String predictUrlPath,
            @Value("${ml.service.live-feed-path}") String liveFeedPath,
            @Value("${ml.service.timeout-seconds}") long timeoutSeconds) {
        this.webClient = webClientBuilder.baseUrl(baseUrl).build();
        this.predictPath = predictPath;
        this.predictUrlPath = predictUrlPath;
        this.liveFeedPath = liveFeedPath;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
    }

    public MlPredictionResponse predict(String newsText) {
        log.debug("Calling ML service POST {}", predictPath);
        try {
            MlPredictionResponse response = webClient.post()
                    .uri(predictPath)
                    .bodyValue(Map.of("newsText", newsText))
                    .retrieve()
                    .onStatus(
                            status -> status.is4xxClientError() || status.is5xxServerError(),
                            res -> res.bodyToMono(String.class)
                                    .flatMap(body -> Mono.error(
                                            new MlServiceException("ML service error: " + body))))
                    .bodyToMono(MlPredictionResponse.class)
                    .timeout(timeout)
                    .block();
            if (response == null)
                throw new MlServiceException("ML service returned an empty response.");
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service. Is it running on port 5001?", e);
        }
    }

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
            if (response == null)
                throw new MlServiceException("ML service returned an empty response for URL prediction.");
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service. Is it running?", e);
        }
    }

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
            if (response == null)
                throw new MlServiceException("ML service returned an empty live-feed response.");
            return response;
        } catch (WebClientException e) {
            throw new MlServiceException("Cannot connect to ML service for live feed.", e);
        }
    }
}
