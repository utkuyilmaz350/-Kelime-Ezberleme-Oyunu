package com.kelimeezberleme.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "UserSettings")
public class UserSettings {
    @Id
    @OneToOne
    @JoinColumn(name = "UserID")
    private User user;
    
    private Integer quizCount = 10;
} 