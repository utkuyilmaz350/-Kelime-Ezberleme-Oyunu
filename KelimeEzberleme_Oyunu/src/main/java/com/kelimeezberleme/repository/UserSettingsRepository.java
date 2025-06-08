package com.kelimeezberleme.repository;

import com.kelimeezberleme.model.UserSettings;
import com.kelimeezberleme.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserSettingsRepository extends JpaRepository<UserSettings, Long> {
    Optional<UserSettings> findByUser(User user);
} 