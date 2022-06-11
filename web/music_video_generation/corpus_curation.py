import warnings
from audio_similarity import *
import config
import pandas as pd
import sklearn
from sklearn.cluster import MiniBatchKMeans
import pickle
import librosa as lr
import string
import cv2
import os
import pickle
import time
from sklearn.decomposition import PCA


def drop_table(cur, table_name):
    cur.execute('select exists(select * from information_schema.tables where table_name=%s)', (table_name,))
    table_exists = cur.fetchone()[0]
     
    if table_exists:
        drop_query = 'drop table ' + table_name
        cur.execute(drop_query)

def feature_selection(features, n_components=None):
    pca = PCA(n_components=n_components)
    pca.fit(features)
    features = pca.transform(features)
    pca_name = './pca_model_' + str(n_components) + '.joblib'
    pickle.dump(pca, open(pca_name.lower(), 'wb'))

    print('n_components_post_feature_selection:', len(features[0]))
    print('explained variance:', np.sum(pca.explained_variance_ratio_))

    return features

def get_cluster_labels(feature_vectors, n_components):
    features = pd.DataFrame(feature_vectors)
    features = features.fillna(features.mean())
    features = feature_selection(features, n_components)
    SEGMENTS_PER_CLUSTER = 50
    n_clusters = round(len(features)/SEGMENTS_PER_CLUSTER)
    batch_size = n_clusters//10
    batch_size = 1 if batch_size < 1 else batch_size

    model = MiniBatchKMeans(n_clusters=n_clusters,
                            random_state=5,
                            batch_size=batch_size,
                            max_iter=1)

    start = time.time()
    cluster_labels = model.fit_predict(features)
    end = time.time()
    print('Training time:', str(end - start), 'seconds')
    model_name = './audio_cluster' + '_' + str(n_components) + '.pkl'
    pickle.dump(model, open(model_name.lower(), 'wb'))

    return cluster_labels, features


def get_song_durations(segments):#d
    durations = {}
    
    for song in segments:
        song_path = '/Volumes/WD_BLACK/' + song
        print('getting duration for:', song_path)
        audio, sample_rate = lr.load(song_path, sr=None)
        duration = lr.get_duration(audio, sample_rate)
        durations[song[:-4]] = duration
        
    durations = pd.DataFrame(list(durations.items()), columns=['Title', 'Duration'])
    # durations.to_csv('./temp/durations.csv', index=False) #d from storage
    return durations


def get_segment_durations(segments, songs_path):
    song_durations = get_song_durations(segments)
    segment_durations = {}
    for segment in segments:
        segment = segment[:-4]
        duration = song_durations.loc[song_durations['Title']==segment, 'Duration']
        segment_durations[segment] = duration.iloc[0]

    with open('./temp/durations.data', 'wb') as f:
        pickle.dump(segment_durations, f)

    return segment_durations
        
        
def populate_database(cur, feature_vectors, segments, songs_path, table_name, n_components, cluster_labels=None, durations=None):
    # with open('./temp/feature_vectors.data', 'rb') as f:
    #     feature_vectors = pickle.load(f)

    if durations is None:
        durations = get_segment_durations(segments, songs_path)
        # with open('./temp/durations.data', 'rb') as f:
        #     durations = pickle.load(f)

    if cluster_labels is None:
        cluster_labels, feature_vectors = get_cluster_labels(feature_vectors, n_components)
    feature_vectors = feature_vectors.tolist()

    for i, cluster_label in enumerate(cluster_labels):
        cluster_label = str(cluster_label)
        feature_vector = str(feature_vectors[i])[1:-1]
        segment = segments[i][:-4]
        duration = str(durations[segment])
        query = 'insert into ' + table_name + ' values (\'{' + feature_vector + '}\', \'' + segment + '\', ' \
                + cluster_label + ', ' + duration + ')'

        cur.execute(query)


def prepare_queries(songs_path, segment_names, cur, table_name, n_components):
    feature_vectors = []

    for i, segment in enumerate(segment_names):
        i += 1
        print('Preparing query', i)
        segment_path = songs_path + segment
        print('Segment path:', segment_path + '\n')
        features = extract_features(segment_path)
        unflattened_stats = generate_feature_stats(features)
        stats = flatten_features(unflattened_stats)

        for j, stat in enumerate(stats):
            stats[j] = stat.item()

        feature_vectors.append(stats)

    # with open('./temp/feature_vectors.data', 'wb') as f:
    #     pickle.dump(feature_vectors, f)

    populate_database(cur, feature_vectors, segment_names, songs_path, table_name, n_components)

def get_segment_names(songs_path='/Volumes/WD_BLACK/'):
    segment_directories = [f + '/' for f in os.listdir(songs_path) if f.endswith('segments')]
    segment_names = []

    for segment_dir in segment_directories:
        full_segment_dir = songs_path + segment_dir 
        
        for segment in os.listdir(full_segment_dir):
            if segment.endswith('.mp4') and not segment.startswith('.'):
                segment_name = segment_dir + segment
                segment_names.append(segment_name)
                
    return segment_names


if __name__ == '__main__':
    exit()#d
    warnings.filterwarnings('ignore')
    songs_path = '/Volumes/WD_BLACK/'
    segment_names = get_segment_names(songs_path)
    
    # with open('./temp/segment_samples.data', 'rb') as f:#d
    #     segment_names = pickle.load(f)

    n_components = get_n_components()
    for n in n_components:
        print('\nn_components:', n)
        table_name = get_table_name()
        con = psycopg2.connect(
                    host='localhost',
                    database='dj_mvp',
                    user='postgres',
                    password=config.password)

        cur = con.cursor()

        table_name += '_' + str(n)
        create_table = 'create table ' + table_name + ' (features float[], name text, cluster_label int, duration float)'
        drop_table(cur, table_name)
        cur.execute(create_table)
        con.commit()

        prepare_queries(songs_path, segment_names, cur, table_name, n)

        con.commit()
        cur.close()
        con.close()
