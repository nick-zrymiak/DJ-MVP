import warnings
from audio_similarity import *

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    corpus_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'
    target_path = corpus_path + 'BarBarBar53.mp4'
#     target_path = corpus_path + 'Alejandro46.mp4'
#     target_path = corpus_path + 'Afrojack5.mp4'
#     target_path = corpus_path + 'Afrojack1.mp4'

    features = extract_features(target_path)
    unflattened_stats = generate_feature_stats(features)
    stats = flatten_features(unflattened_stats)
    closest_segment = get_closest_segment(stats)
    print(closest_segment)#d
    