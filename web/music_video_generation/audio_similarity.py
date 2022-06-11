import librosa as lr
import numpy as np
import statistics
import psycopg2
from os import listdir
from os.path import isfile, join
import pandas as pd
import pickle
import math

def get_table_name():
    return 'full_corpus'

def get_n_components():
    return [100]

def flatten_features(unflattened_stats):
    stats = []
    
    for feature in unflattened_stats:
        for window in feature:
            for stat in window:
                stats.append(stat)
    
    return stats

def generate_feature_stats(features):
    unflattened_stats = []
    
    for j, feature in enumerate(features):
        if feature.ndim < 2:
            feature = np.reshape(feature, (1, -1))
            features[j] = feature
        feature_stats = []
        for i, feature_group in enumerate(feature):
            feature_group = (feature_group - min(feature_group)) / (max(feature_group) - min(feature_group)) # normalize data
            mean = sum(feature_group) / len(feature_group)
            std = np.std(feature_group)
            feature_stats.append([mean, std])
        
        unflattened_stats.append(feature_stats)
    
    return unflattened_stats

def extract_features(audio_path=None, audio=None, sample_rate=None):
    if audio_path != None:
        audio, sample_rate = lr.load(audio_path, sr=None) # setting sr=None preserves original sample rate
        
    window_length = round(.023 * sample_rate) # 23ms window
    features = []
    hop_length = round(window_length / 2) # 50% overlap
    window = 'hann'

    melspectrogram = lr.feature.melspectrogram(audio,
                                               sample_rate,
                                               n_fft=window_length,
                                               window=window,
                                               hop_length=hop_length)

    mfcc = lr.feature.mfcc(audio,
                           sample_rate,
                           n_mfcc=12,
                           n_fft=window_length,
                           window=window,
                           hop_length=hop_length)

    spectral_contrast = lr.feature.spectral_contrast(audio,
                                                     sample_rate,
                                                     n_fft=window_length,
                                                     n_bands=6,
                                                     window=window,
                                                     hop_length=hop_length)

    spectral_flatness = lr.feature.spectral_flatness(audio,
                                                     n_fft=window_length,
                                                     window=window,
                                                     hop_length=hop_length)

    spectral_rolloff = lr.feature.spectral_rolloff(audio,
                                                   sample_rate,
                                                   n_fft=window_length,
                                                   window=window,
                                                   hop_length=hop_length)

    zero_crossing_rate = lr.feature.zero_crossing_rate(audio,
                                                       window_length,
                                                       hop_length=hop_length)

    onset_strength = lr.onset.onset_strength(audio,
                                             sample_rate,
                                             **{'hop_length': hop_length,
                                                'n_fft': window_length,
                                                'window': window})

    features.extend([
        melspectrogram,
        mfcc,
        spectral_contrast,
        spectral_flatness,
        spectral_rolloff,
        zero_crossing_rate,
        onset_strength
    ])
    
    return features

def get_segments_from_database(cur, 
                               cluster_label, 
                               duration, 
                               min_duration_corpus_segments, 
                               max_duration_corpus_segments, 
                               blacklist_query_addendum):
    
    min_duration_cutoff = .75 * duration
    max_duration_cutoff = 1.25 * duration
    
    if min_duration_cutoff < min_duration_corpus_segments:
        min_duration_cutoff = min_duration_corpus_segments
        max_duration_cutoff = 1.25 * min_duration_corpus_segments
    
    if max_duration_cutoff > max_duration_corpus_segments:
        max_duration_cutoff = max_duration_corpus_segments
        min_duration_cutoff = .75 * max_duration_corpus_segments
    
    fetch_cluster = 'select * from ' + get_table_name() + ' where cluster_label = ' + str(cluster_label) \
                    + ' and duration between ' + str(min_duration_cutoff) + ' and ' + str(max_duration_cutoff) \
                    + blacklist_query_addendum
                    
    cur.execute(fetch_cluster)
    candidate_segments = cur.fetchall()
    
    return candidate_segments

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
                       blacklist_query_addendum):
    
    cluster_centers[np.argmin(cluster_centers)] = float('inf')
    new_cluster_label = np.argmin(cluster_centers)

    candidate_segments = get_segments_from_database(cur, 
                                          new_cluster_label, 
                                          duration, 
                                          min_duration, 
                                          max_duration, 
                                          blacklist_query_addendum)
    
    return candidate_segments

def get_closest_segment(segment_feature_vector, 
                        current_closest_segments, 
                        duration, 
                        blacklist_query_addendum,
                        running_with_ide):

    model = None     
    if running_with_ide:
        import config
        model = pickle.load(open('audio_cluster_100.pkl', 'rb'))
    else:
        import music_video_generation.config as config
        model = pickle.load(open('music_video_generation/audio_cluster_100.pkl', 'rb'))
     
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
    
    fetch_num_clusters = 'select count (distinct cluster_label) from ' + get_table_name()
    cur.execute(fetch_num_clusters)
    num_clusters = cur.fetchall()
    num_clusters = num_clusters[0][0]
     
    min_duration = get_min_duration(cur)
    max_duration = get_max_duration(cur)
    
    segment_feature_vector = pd.DataFrame(segment_feature_vector).T
    predicted_label = model.predict(segment_feature_vector)
    candidate_segments = get_segments_from_database(cur, 
                                          predicted_label[0], 
                                          duration, 
                                          min_duration, 
                                          max_duration, 
                                          blacklist_query_addendum)
     
    closest_segment = None
    min_dist = float('inf')
    exhausted_clusters = 0
    cluster_centers = model.transform(segment_feature_vector)
    cluster_centers = cluster_centers[0]
    while True:
        for cadidate_segment in candidate_segments:
            # retrieve cadidate_segment with minimum distance
            features = cadidate_segment[0]
            
            name = cadidate_segment[1]
            segment_feature_vector_np = np.array(segment_feature_vector)
            dist = np.linalg.norm(segment_feature_vector_np - np.array(features))
            
            if name not in current_closest_segments:
                if dist < min_dist:
                    min_dist = dist
                    closest_segment = name
                     
        if closest_segment is None:
            exhausted_clusters += 1
            
            if exhausted_clusters == num_clusters:
                print('No candidate segments in any cluster')
            
            candidate_segments = widen_search_space(duration, 
                                                   cur, 
                                                   min_duration, 
                                                   max_duration, 
                                                   cluster_centers, 
                                                   blacklist_query_addendum)
        else:
            break
     
    return closest_segment
