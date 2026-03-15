package com.fakenews.backend.repository;

import com.fakenews.backend.model.NewsAnalysis;
import com.fakenews.backend.model.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

/**
 * Spring Data repository for NewsAnalysis persistence.
 */
public interface NewsAnalysisRepository extends JpaRepository<NewsAnalysis, Long> {

    /**
     * Paginated history for a specific user (newest first via Sort in Pageable).
     */
    Page<NewsAnalysis> findByUser(User user, Pageable pageable);

    /** Non-paginated list for a specific user. */
    List<NewsAnalysis> findByUserOrderByCreatedAtDesc(User user);

    /** Total prediction count for a user. */
    long countByUser(User user);
}
