package com.fakenews.backend.controller;

import com.fakenews.backend.dto.AnalyzeUrlRequest;
import com.fakenews.backend.dto.NewsAnalysisResponse;
import com.fakenews.backend.dto.PredictRequest;
import com.fakenews.backend.service.NewsAnalysisService;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/news")
public class NewsController {

    private final NewsAnalysisService newsAnalysisService;

    public NewsController(NewsAnalysisService newsAnalysisService) {
        this.newsAnalysisService = newsAnalysisService;
    }

    @PostMapping("/predict")
    public ResponseEntity<NewsAnalysisResponse> predict(
            @Valid @RequestBody PredictRequest request,
            Authentication authentication) {
        return ResponseEntity.ok(newsAnalysisService.predict(request, authentication.getName()));
    }

    @PostMapping("/analyze-url")
    public ResponseEntity<NewsAnalysisResponse> analyzeUrl(
            @Valid @RequestBody AnalyzeUrlRequest request,
            Authentication authentication) {
        return ResponseEntity.ok(newsAnalysisService.analyzeUrl(request.getUrl(), authentication.getName()));
    }

    @GetMapping("/live-feed")
    public ResponseEntity<Map<String, Object>> liveFeed(
            @RequestParam(defaultValue = "5") int maxPerSource,
            Authentication authentication) {
        List<NewsAnalysisResponse> articles = newsAnalysisService
                .loadAndSaveLiveFeed(authentication.getName(), maxPerSource);
        return ResponseEntity.ok(Map.of(
                "articles", articles,
                "total", articles.size(),
                "savedToDb", true));
    }

    @GetMapping("/history")
    public ResponseEntity<Page<NewsAnalysisResponse>> getHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            Authentication authentication) {
        return ResponseEntity.ok(newsAnalysisService.getHistory(authentication.getName(), page, size));
    }

    @DeleteMapping("/history/{id}")
    public ResponseEntity<Void> deleteHistory(
            @PathVariable Long id,
            Authentication authentication) {
        newsAnalysisService.deleteHistory(id, authentication.getName());
        return ResponseEntity.noContent().build();
    }
}
