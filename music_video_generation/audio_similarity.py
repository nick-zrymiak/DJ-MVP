import librosa as lr
import numpy as np
import statistics
import psycopg2
from os import listdir
from os.path import isfile, join
import config
import pandas as pd
import pickle
import math

def get_table_name():
    return 'new_corpus'

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

def extract_features(audio_path=None, audio=None, sample_rate=None):
    if audio_path != None:
        audio, sample_rate = lr.load(audio_path, sr=None) # setting sr=None preserves original sample rate
        
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

def get_segments_from_database(cur, 
                               cluster_label, 
                               duration, 
                               min_duration_corpus_segments, 
                               max_duration_corpus_segments, 
                               blacklist_query_addendum, 
                               hls_query_addendum):
    
    min_duration = .75 * duration
    max_duration = 1.25 * duration
    
    if min_duration < min_duration_corpus_segments:
        min_duration = min_duration_corpus_segments
        max_duration = 1.25 * min_duration_corpus_segments
    
    if max_duration > max_duration_corpus_segments:
        max_duration = max_duration_corpus_segments
        min_duration = .75 * max_duration_corpus_segments
    
    fetch_cluster = 'select * from ' + get_table_name() + ' where cluster_label = ' + str(cluster_label) \
                    + blacklist_query_addendum + ' and ' + hls_query_addendum
                    
    # check if all clusters have been searched, in which case widen duration range maybe and
    # retry all clusters
                    
    cur.execute(fetch_cluster)
    segments = cur.fetchall()
    
    return segments

def get_min_duration(cur):
    min_duration = 'select min(duration) from ' + get_table_name()
    cur.execute(min_duration)
    min_duration = cur.fetchall()
    min_duration = min_duration[0][0]
    return min_duration

def get_max_duration(cur):
    max_duration = 'select max(duration) from ' + get_table_name()
    cur.execute(max_duration)
    max_duration = cur.fetchall()
    max_duration = max_duration[0][0]
    return max_duration

def widen_search_space(duration, 
                       cur, 
                       min_duration, 
                       max_duration, 
                       cluster_centers, 
                       blacklist_query_addendum, 
                       hls_query_addendum):
    
    cluster_centers[np.argmin(cluster_centers)] = float('inf')
    new_cluster_label = np.argmin(cluster_centers)

    segments = get_segments_from_database(cur, 
                                          new_cluster_label, 
                                          duration, 
                                          min_duration, 
                                          max_duration, 
                                          blacklist_query_addendum,
                                          hls_query_addendum)

def get_closest_segment(target_features, 
                        current_closest_segments, 
                        duration, 
                        blacklist_query_addendum,
                        hls_query_addendum):
     
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
     
    min_duration = get_min_duration(cur)
    max_duration = get_max_duration(cur)
     
    model = pickle.load(open('audio_cluster.pkl', 'rb'))
    df_features = pd.DataFrame(target_features).T
    predicted_label = model.predict(df_features)
    segments = get_segments_from_database(cur, 
                                          predicted_label[0], 
                                          duration, 
                                          min_duration, 
                                          max_duration, 
                                          blacklist_query_addendum, 
                                          hls_query_addendum)
     
    closest_segment = None
    min_dist = float('inf')
    exhausted_clusters = 0
    cluster_centers = model.transform(df_features)
    cluster_centers = cluster_centers[0]
    while True:
        for segment in segments:
            # retrieve segment with minimum distance
            features = segment[0]
            
            for i in range(len(features)):#d
                if math.isnan(features[i]):#d
                    features[i] = target_features[i]#d
            
            name = segment[1]
            dist = np.linalg.norm(np.array(target_features) - np.array(features))
             
            if name not in current_closest_segments:
                if dist < min_dist:
                    min_dist = dist
                    closest_segment = name
                     
        if closest_segment is None:
            widen_search_space(duration, 
                               cur, 
                               min_duration, 
                               max_duration, 
                               cluster_centers, 
                               blacklist_query_addendum, 
                               hls_query_addendum)
        else:
            break
     
    return closest_segment
