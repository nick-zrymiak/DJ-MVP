import warnings
from audio_similarity import *
import config
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
import pickle
import librosa as lr
import string
import cv2

def drop_table(cur, table_name):
    cur.execute('select exists(select * from information_schema.tables where table_name=%s)', (table_name,))
    table_exists = cur.fetchone()[0]
     
    if table_exists:
        drop_query = 'drop table ' + table_name
        cur.execute(drop_query)

def get_cluster_labels(feature_vectors):
    features = pd.DataFrame(feature_vectors)
    features = features.fillna(features.mean())
    SEGMENTS_PER_CLUSTER = 50
    model = KMeans(n_clusters=round(len(features)/SEGMENTS_PER_CLUSTER), random_state=5)
    cluster_labels = model.fit_predict(features)
    pickle.dump(model, open('./audio_cluster.pkl', 'wb'))
    return cluster_labels

def get_song_durations(songs_path):#d
    songs = [song for song in listdir(songs_path) if song.endswith('.mp4')]
    durations = {}
    
    for song in songs:
        print(song)
        song_path = songs_path + song
        audio, sample_rate = lr.load(song_path, sr=None)
        duration = lr.get_duration(audio, sample_rate)
        durations[song[:-4]] = duration
        
    durations = pd.DataFrame(list(durations.items()), columns=['Title', 'Duration'])
    durations.to_csv('./temp/durations.csv', index=False) #d from storage
    return durations

def get_segment_durations(segments, songs_path):
#     song_durations = pd.read_csv('./temp/durations.csv')
    song_durations = get_song_durations(songs_path)
    segment_durations = {}
    
    for segment in segments:    
        segment = segment[:-4]
        duration = song_durations.loc[song_durations['Title']==segment, 'Duration']
        segment_durations[segment] = duration.iloc[0]
        
    return segment_durations

def get_visual_features(segments, songs_path):
    visual_features = []

    for i, segment in enumerate(segments):
        print('extracting visuals for video', i)
        segment_path = songs_path + segment
        visual_features.append(extract_visual_features(segment_path))
        
    return visual_features
        
def populate_database(cur, feature_vectors, segments, songs_path, table_name, cluster_labels=None, durations=None):
    if cluster_labels is None:
        cluster_labels = get_cluster_labels(feature_vectors)

    if durations is None:
        durations = get_segment_durations(segments, songs_path)
        
    visual_features = get_visual_features(segments, songs_path)
    cluster_labels_query = ''
    
    for i, cluster_label in enumerate(cluster_labels):
        cluster_label = str(cluster_label)
        feature_vector = str(feature_vectors[i])[1:-1]
        clip_visual_features = visual_features[i]
        segment = segments[i][:-4]
        duration = str(durations[segment])
        hue = str(clip_visual_features['hue'])
        lightness = str(clip_visual_features['lightness'])
        saturation = str(clip_visual_features['saturation'])
        query = 'insert into ' + table_name + ' values (\'{' + feature_vector + '}\', \'' + segment + '\', ' \
                + cluster_label + ', ' + duration + ', ' + hue + ', ' + lightness + ', ' + saturation + ')'
                
        cur.execute(query)

def get_hls(image):
    hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS_FULL)
    avg_hue = hls[:, :, 0].mean()
    avg_lightness = hls[:, :, 1].mean()
    avg_saturation = hls[:, :, 2].mean()
    
    return avg_hue, avg_lightness, avg_saturation

def extract_visual_features(clip_path):
    cap = cv2.VideoCapture(clip_path)
    
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_hue = 0
    video_lightness = 0
    video_saturation = 0
    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        
        if ret == False:
            break
        
        if i in [0, int(num_frames/2), num_frames-1]:
            frame_hue, frame_lightness, frame_saturation = get_hls(frame)
            video_hue += frame_hue
            video_lightness += frame_lightness
            video_saturation += frame_saturation
        
        i += 1
    
    NUM_FRAMES_USED = 3
    features = {'hue': video_hue/NUM_FRAMES_USED, 
                'lightness': video_lightness/NUM_FRAMES_USED, 
                'saturation': video_saturation/NUM_FRAMES_USED}
     
    return features

def prepare_queries(songs_path, segment_names, cur, table_name):
    feature_vectors = []
    
    for i, segment in enumerate(segment_names):
        i += 1
        print('Preparing query', i)
        segment_path = songs_path + segment
        features = extract_features(segment_path)
        unflattened_stats = generate_feature_stats(features)
        stats = flatten_features(unflattened_stats)
        
        for i, stat in enumerate(stats):
            stats[i] = np.asscalar(stat)
        
        feature_vectors.append(stats)
        
    populate_database(cur, feature_vectors, segment_names, songs_path, table_name)

def populate_visuals(cur, songs_path, table_name): #d
    fetch_cluster = 'select * from ' + table_name
    cur.execute(fetch_cluster)
    
    segments = cur.fetchall()
    segments = list(map(list, zip(*segments)))
    feature_vectors = segments[0]
    segment_names = [name + '.mp4' for name in segments[1]]
    cluster_labels = segments[2]
    durations = segments[3]
    
    populate_database(cur, feature_vectors, segment_names, songs_path, table_name, cluster_labels, durations)

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    songs_path = '/Users/Nick/Desktop/misc/djmvp/segments/'
    segment_names = [segment for segment in listdir(songs_path) if segment.endswith('.mp4')]
    
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()

    table_name = get_table_name()    
#     populate_visuals(cur, songs_path, table_name)    
#     drop_table(cur, table_name)

    create_table = 'create table ' + table_name + ' (features float[], name text, cluster_label int, duration float, hue float, lightness float, saturation float)'
#     cur.execute(create_table)
#     con.commit()
    
    prepare_queries(songs_path, segment_names, cur, table_name)
        
    con.commit()
    cur.close()
    con.close()
