package com.kelimeezberleme.repository;

import com.kelimeezberleme.model.Word;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface WordRepository extends JpaRepository<Word, Long> {
    List<Word> findByEngWordNameContainingOrTurWordNameContaining(String engWord, String turWord);
    
    @Query(value = "SELECT * FROM Words ORDER BY RANDOM() LIMIT ?1", nativeQuery = true)
    List<Word> findRandomWords(int limit);
} 