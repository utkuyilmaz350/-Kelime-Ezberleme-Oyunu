package com.kelimeezberleme.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "WordSamples")
public class WordSample {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long wordSamplesId;
    
    @ManyToOne
    @JoinColumn(name = "WordID")
    private Word word;
    
    private String samples;
} 