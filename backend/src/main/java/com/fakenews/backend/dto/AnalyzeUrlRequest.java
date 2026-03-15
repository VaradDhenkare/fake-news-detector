package com.fakenews.backend.dto;

import jakarta.validation.constraints.NotBlank;

/** Payload for POST /api/news/analyze-url */
public class AnalyzeUrlRequest {

    @NotBlank(message = "url must not be blank")
    private String url;

    public AnalyzeUrlRequest() {
    }

    public AnalyzeUrlRequest(String url) {
        this.url = url;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }
}
