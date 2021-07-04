import warnings
from audio_similarity import *
import config

def prepare_queries(corpus_path, segment_names, cur):
    for i, segment in enumerate(segment_names):
        i += 1
        print('Prepared query', i)
        segment_path = corpus_path + segment
        features = extract_features(segment_path)
        unflattened_stats = generate_feature_stats(features)
        stats = flatten_features(unflattened_stats)
        for i, stat in enumerate(stats):
            stats[i] = np.asscalar(stat)
        
        stats = str(stats)
        query = 'insert into segment_features values (\'{' + stats[1:-1] + '}\', \'' + segment[:-4] + '\')'
        cur.execute(query)
        con.commit()

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    corpus_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'

    segment_names = [segment for segment in listdir(corpus_path) if segment.endswith('.mp4')]
    segment_names = segment_names[prev_segments:next_segments]
    
    con = psycopg2.connect(
                host='localhost',
                database='dj_mvp',
                user='postgres',
                password=config.password)    
    cur = con.cursor()
    prepare_queries(corpus_path, segment_names, cur)
        
    cur.close()
    con.close()
