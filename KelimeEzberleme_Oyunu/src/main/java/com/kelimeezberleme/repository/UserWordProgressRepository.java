package com.kelimeezberleme.repository;

import com.kelimeezberleme.model.UserWordProgress;
import com.kelimeezberleme.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface UserWordProgressRepository extends JpaRepository<UserWordProgress, Long> {
    List<UserWordProgress> findByUser(User user);
    
    @Query("SELECT COUNT(u) FROM UserWordProgress u WHERE u.user = ?1 AND u.correctCount >= 6")
    Long countKnownWords(User user);
    
    @Query("SELECT u FROM UserWordProgress u WHERE u.user = ?1 AND u.correctCount < 6 ORDER BY u.lastTested ASC")
    List<UserWordProgress> findWordsToReview(User user);
} 