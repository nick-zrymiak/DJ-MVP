import warnings
from audio_similarity import *
import config
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
import pickle
import librosa as lr
import string

def drop_table(cur):
    cur.execute('select exists(select * from information_schema.tables where table_name=%s)', ('segment_features',))
    table_exists = cur.fetchone()[0]
     
    if table_exists:
        cur.execute('drop table segment_features')

def get_cluster_labels(feature_vectors):
    features = pd.DataFrame(feature_vectors)
    features = features.fillna(features.mean())
    SEGMENTS_PER_CLUSTER = 50
    model = KMeans(n_clusters=round(len(features)/SEGMENTS_PER_CLUSTER), random_state=5)
    cluster_labels = model.fit_predict(features)
    pickle.dump(model, open('./audio_cluster.pkl', 'wb'))
    return cluster_labels

def get_song_durations():#d
    songs_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'
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

def get_segment_durations(segments):
#     song_durations = pd.read_csv('./temp/durations.csv')
    song_durations = get_song_durations()
    segment_durations = {}
    
    for segment in segments:    
        segment = segment[:-4]
        duration = song_durations.loc[song_durations['Title']==segment, 'Duration']
        segment_durations[segment] = duration.iloc[0]
        
    return segment_durations

def populate_database(cur, feature_vectors, segments, cluster_labels):#d remove cluster_labels param and uncomment line below
#     cluster_labels = get_cluster_labels(feature_vectors)
    durations = get_segment_durations(segments)
    cluster_labels_query = ''
    
    for i, cluster_label in enumerate(cluster_labels):
        cluster_label = str(cluster_label)
        feature_vector = str(feature_vectors[i])[1:-1]
        segment = segments[i][:-4]
        duration = str(durations[segment])
        query = 'insert into segment_features values (\'{' + feature_vector + '}\', \'' + segment + '\', ' + cluster_label + ', ' + duration + ')'
        cur.execute(query)

def prepare_queries(songs_path, segment_names, cur):
    feature_vectors = []
    
    for i, segment in enumerate(segment_names):
        i += 1
        print('Prepared query', i)
        segment_path = songs_path + segment
        features = extract_features(segment_path)
        unflattened_stats = generate_feature_stats(features)
        stats = flatten_features(unflattened_stats)
        
        for i, stat in enumerate(stats):
            stats[i] = np.asscalar(stat)
        
        feature_vectors.append(stats)
        
    populate_database(cur, feature_vectors, segment_names)

def populate_durations(cur): #d
    fetch_cluster = 'select * from segment_features'
    cur.execute(fetch_cluster)
    
    segments = cur.fetchall()
    segments = list(map(list, zip(*segments)))
    feature_vectors = segments[0]
    segment_names = [name + '.mp4' for name in segments[1]]
    cluster_labels = segments[2]
    
    populate_database(cur, feature_vectors, segment_names, cluster_labels)

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    songs_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'

    segment_names = [segment for segment in listdir(songs_path) if segment.endswith('.mp4')]
    
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
    
    populate_durations(cur)
    
#     drop_table(cur)
#     create_table = 'create table segment_features (features float[], name text, cluster_label int, duration float)'
#     cur.execute(create_table)
#     con.commit()
    
#     prepare_queries(songs_path, segment_names, cur)
        
    con.commit()
    cur.close()
    con.close()
