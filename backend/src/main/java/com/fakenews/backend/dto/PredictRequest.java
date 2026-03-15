package com.fakenews.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** Payload for POST /api/news/predict */
public class PredictRequest {

    @NotBlank(message = "newsText must not be blank")
    @Size(min = 10, max = 10000, message = "newsText must be between 10 and 10 000 characters")
    private String newsText;

    public PredictRequest() {
    }

    public PredictRequest(String newsText) {
        this.newsText = newsText;
    }

    public String getNewsText() {
        return newsText;
    }

    public void setNewsText(String newsText) {
        this.newsText = newsText;
    }
}
