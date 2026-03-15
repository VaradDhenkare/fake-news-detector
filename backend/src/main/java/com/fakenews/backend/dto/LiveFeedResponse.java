package com.fakenews.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

/**
 * Maps the full JSON response from ML service GET /live-feed.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class LiveFeedResponse {
    private List<LiveFeedArticleDto> articles;
    private Integer total;
    private String fetchedAt;

    public LiveFeedResponse() {
    }

    public List<LiveFeedArticleDto> getArticles() {
        return articles;
    }

    public void setArticles(List<LiveFeedArticleDto> articles) {
        this.articles = articles;
    }

    public Integer getTotal() {
        return total;
    }

    public void setTotal(Integer total) {
        this.total = total;
    }

    public String getFetchedAt() {
        return fetchedAt;
    }

    public void setFetchedAt(String fetchedAt) {
        this.fetchedAt = fetchedAt;
    }
}
