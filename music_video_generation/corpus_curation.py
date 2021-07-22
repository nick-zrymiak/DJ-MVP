import warnings
from audio_similarity import *
import config
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
import pickle

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

def populate_database(cur, feature_vectors, segments):
    cluster_labels = get_cluster_labels(feature_vectors)
    cluster_labels_query = ''
    
    for i, cluster_label in enumerate(cluster_labels):
        cluster_label = str(cluster_label)
        feature_vector = str(feature_vectors[i])[1:-1]
        query = 'insert into segment_features values (\'{' + feature_vector + '}\', \'' + segments[i][:-4] + '\', ' + cluster_label + ')'
        cur.execute(query)

def prepare_queries(corpus_path, segment_names, cur):
    feature_vectors = []
    
    for i, segment in enumerate(segment_names):
        i += 1
        print('Prepared query', i)
        segment_path = corpus_path + segment
        features = extract_features(segment_path)
        unflattened_stats = generate_feature_stats(features)
        stats = flatten_features(unflattened_stats)
        
        for i, stat in enumerate(stats):
            stats[i] = np.asscalar(stat)
        
        feature_vectors.append(stats)
        
    populate_database(cur, feature_vectors, segment_names)

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    corpus_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'

    segment_names = [segment for segment in listdir(corpus_path) if segment.endswith('.mp4')]
    
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
    
#     drop_table(cur)
    create_table = 'create table segment_features (features float[], name text, cluster_label int)'
    cur.execute(create_table)
    con.commit()
    
    prepare_queries(corpus_path, segment_names, cur)
        
    con.commit()
    cur.close()
    con.close()
