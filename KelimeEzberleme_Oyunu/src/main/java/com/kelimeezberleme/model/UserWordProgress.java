package com.kelimeezberleme.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "UserWordProgress")
public class UserWordProgress {
    @Id
    @ManyToOne
    @JoinColumn(name = "UserID")
    private User user;
    
    @Id
    @ManyToOne
    @JoinColumn(name = "WordID")
    private Word word;
    
    private Integer correctCount = 0;
    
    private LocalDate lastTested;
} 