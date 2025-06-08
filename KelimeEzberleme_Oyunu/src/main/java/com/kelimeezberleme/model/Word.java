package com.kelimeezberleme.model;

import jakarta.persistence.*;
import lombok.Data;
import java.util.List;

@Data
@Entity
@Table(name = "Words")
public class Word {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long wordId;
    
    @Column(name = "EngWordName")
    private String engWordName;
    
    @Column(name = "TurWordName")
    private String turWordName;
    
    private String picture;
    
    private String pronunciation;
    
    @OneToMany(mappedBy = "word", cascade = CascadeType.ALL)
    private List<WordSample> samples;
} 