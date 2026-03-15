package com.fakenews.backend.service;

import com.fakenews.backend.dto.*;
import com.fakenews.backend.exception.ResourceNotFoundException;
import com.fakenews.backend.model.NewsAnalysis;
import com.fakenews.backend.model.User;
import com.fakenews.backend.repository.NewsAnalysisRepository;
import com.fakenews.backend.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class NewsAnalysisService {

        private static final Logger log = LoggerFactory.getLogger(NewsAnalysisService.class);

        private final MlClientService mlClientService;
        private final NewsAnalysisRepository newsAnalysisRepository;
        private final UserRepository userRepository;

        public NewsAnalysisService(MlClientService mlClientService,
                        NewsAnalysisRepository newsAnalysisRepository,
                        UserRepository userRepository) {
                this.mlClientService = mlClientService;
                this.newsAnalysisRepository = newsAnalysisRepository;
                this.userRepository = userRepository;
        }

        private User getUser(String username) {
                return userRepository.findByUsername(username)
                                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + username));
        }

        private NewsAnalysisResponse toDto(NewsAnalysis e) {
                NewsAnalysisResponse r = new NewsAnalysisResponse();
                r.setId(e.getId());
                r.setNewsText(e.getNewsText());
                r.setPrediction(e.getPrediction());
                r.setConfidence(e.getConfidence());
                r.setCreatedAt(e.getCreatedAt());
                r.setSourceUrl(e.getSourceUrl());
                r.setSourceName(e.getSourceName());
                r.setArticleTitle(e.getArticleTitle());
                return r;
        }

        private NewsAnalysis save(User user, String newsText, String prediction,
                        Double confidence, String sourceUrl,
                        String sourceName, String articleTitle) {
                NewsAnalysis entity = new NewsAnalysis();
                entity.setUser(user);
                entity.setNewsText(newsText);
                entity.setPrediction(prediction);
                entity.setConfidence(confidence);
                entity.setCreatedAt(LocalDateTime.now());
                entity.setSourceUrl(sourceUrl);
                entity.setSourceName(sourceName);
                entity.setArticleTitle(articleTitle);
                return newsAnalysisRepository.save(entity);
        }

        public NewsAnalysisResponse predict(PredictRequest request, String username) {
                User user = getUser(username);
                MlPredictionResponse ml = mlClientService.predict(request.getNewsText());
                NewsAnalysis saved = save(user, request.getNewsText(), ml.getPrediction(),
                                ml.getConfidence(), null, null, null);
                return toDto(saved);
        }

        public NewsAnalysisResponse analyzeUrl(String url, String username) {
                User user = getUser(username);
                MlUrlPredictionResponse ml = mlClientService.predictUrl(url);
                String textToStore = ml.getText() != null ? ml.getText()
                                : ml.getTextSnippet() != null ? ml.getTextSnippet() : url;
                NewsAnalysis saved = save(user, textToStore, ml.getPrediction(), ml.getConfidence(),
                                ml.getUrl(), ml.getSource(), ml.getTitle());
                log.info("URL analysis saved [id={}] for user '{}': {}", saved.getId(), username, url);
                return toDto(saved);
        }

        public List<NewsAnalysisResponse> loadAndSaveLiveFeed(String username, int maxPerSource) {
                User user = getUser(username);
                LiveFeedResponse feedResponse = mlClientService.getLiveFeed(maxPerSource);
                List<NewsAnalysisResponse> results = feedResponse.getArticles().stream()
                                .map(article -> {
                                        String text = article.getText() != null && !article.getText().isBlank()
                                                        ? article.getText()
                                                        : article.getTitle() + ". " + article.getSummary();
                                        NewsAnalysis saved = save(user, text, article.getPrediction(),
                                                        article.getConfidence(), article.getUrl(),
                                                        article.getSource(), article.getTitle());
                                        NewsAnalysisResponse dto = toDto(saved);
                                        dto.setSummary(article.getSummary());
                                        dto.setSourceIcon(article.getSourceIcon());
                                        dto.setPublished(article.getPublished());
                                        return dto;
                                })
                                .collect(Collectors.toList());
                log.info("Live feed: {} articles saved for user '{}'", results.size(), username);
                return results;
        }

        public Page<NewsAnalysisResponse> getHistory(String username, int page, int size) {
                User user = getUser(username);
                Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
                return newsAnalysisRepository.findByUser(user, pageable).map(this::toDto);
        }

        public void deleteHistory(Long id, String username) {
                User user = getUser(username);
                NewsAnalysis entry = newsAnalysisRepository.findById(id)
                                .orElseThrow(() -> new ResourceNotFoundException("Analysis not found: " + id));
                if (!entry.getUser().getId().equals(user.getId())) {
                        throw new ResourceNotFoundException("Analysis not found for this user.");
                }
                newsAnalysisRepository.delete(entry);
                log.info("Deleted analysis [id={}] for user '{}'", id, username);
        }
}
