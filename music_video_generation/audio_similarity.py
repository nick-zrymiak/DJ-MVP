import librosa as lr
import numpy as np
import statistics
import psycopg2
from os import listdir
from os.path import isfile, join
import config

def flatten_features(unflattened_stats):
    stats = []
    
    for feature in unflattened_stats:
        for window in feature:
            for stat in window:
                stats.append(stat)
                
    return stats

def generate_feature_stats(features):
    unflattened_stats = []
    
    for feature in features:
        feature_stats = []
        for i, window in enumerate(feature):
            window = (window - min(window)) / (max(window) - min(window))
            mean = sum(window) / len(window)
            std = np.std(window)
            feature_stats.append([mean, std])
        
        unflattened_stats.append(feature_stats)
    
    return unflattened_stats

def extract_features(audio_path):
    audio, sample_rate = lr.load(audio_path, sr=None) #setting sr=None preserves original sample rate
    window_length = round(.023 * sample_rate) # 23ms window
    features = []
    hop_length = round(window_length / 2) #50% overlap
    
    chroma_cens = lr.feature.chroma_cens(audio, 
                                         sample_rate, 
                                         n_chroma=12, 
                                         smoothing_window='hann')
    
    melspectrogram = lr.feature.melspectrogram(audio,
                                               sample_rate,
                                               n_fft=window_length,
                                               window='hann',
                                               hop_length=hop_length)
    
    mfcc = lr.feature.mfcc(audio, 
                           sample_rate, 
                           n_mfcc=20, 
                           n_fft=window_length, 
                           window='hann', 
                           hop_length=hop_length)
    
    spectral_contrast = lr.feature.spectral_contrast(audio,
                                                     sample_rate,
                                                     n_fft=window_length,
                                                     n_bands=6,
                                                     window='hann',
                                                     hop_length=hop_length)
    
    spectral_flatness = lr.feature.spectral_flatness(audio,
                                                     n_fft=window_length,
                                                     window='hann',
                                                     hop_length=hop_length)
    
    spectral_rolloff = lr.feature.spectral_rolloff(audio, 
                                                   sample_rate,
                                                   n_fft=window_length, 
                                                   window='hann', 
                                                   hop_length=hop_length)
    
    zero_crossing_rate = lr.feature.zero_crossing_rate(audio,
                                                       window_length,
                                                       hop_length=hop_length)

    features.extend([chroma_cens, 
                     melspectrogram, 
                     mfcc, 
                     spectral_contrast, 
                     spectral_flatness, 
                     spectral_rolloff, 
                     zero_crossing_rate])
    
    return features

def get_closest_segment(target_features):
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
    cur.execute('select * from segment_features')
    segments = cur.fetchall()
    
    closest_segment = None
    min_dist = float('inf')
    for segment in segments:
        features = segment[0]
        name = segment [1]
        
        if name != 'Alejandro46' and name != 'BarBarBar53' and name != 'Afrojack5':#d
            dist = np.linalg.norm(np.array(target_features)-np.array(features))
            if dist < min_dist:
                min_dist = dist
                closest_segment = segment
    
    name = closest_segment[1]
    return name
    