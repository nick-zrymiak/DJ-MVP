import warnings
import os
from moviepy.editor import *
import moviepy as mp
import math
import string
import librosa as lr
import numpy as np
import pandas as pd
import time
import pickle

def segment_audio_by_beats(beat_frames, hop_length=512):
    beat_sample_cutoffs = [i * hop_length for i in beat_frames]
    return beat_sample_cutoffs

def get_segment_feature_vectors(beat_sample_cutoffs, audio, sample_rate):
    segment_feature_vectors = []
    for i, beat_sample_cutoff in enumerate(beat_sample_cutoffs):
        if i < len(beat_sample_cutoffs) - 1:
            print('beat:', i)
            beat_sample = audio[beat_sample_cutoff:beat_sample_cutoffs[i+1]]
            features = extract_features(audio=beat_sample, sample_rate=sample_rate)
            unflattened_stats = generate_feature_stats(features)
            stats = flatten_features(unflattened_stats)
            segment_feature_vectors.append(stats)
        
    return segment_feature_vectors

def clean_feature_vectors(segment_feature_vectors):
    segment_feature_vectors = pd.DataFrame(segment_feature_vectors)
    segment_feature_vectors = segment_feature_vectors.fillna(segment_feature_vectors.mean())

    pca_name = './pca_model_100.joblib'
    pca = pickle.load(open(pca_name, 'rb'))
    segment_feature_vectors = pca.transform(segment_feature_vectors)

    return segment_feature_vectors.tolist()

def blacklist_overused_song(max_segments_per_song, song_counts, blacklist_query_addendum, closest_segment):
    song_of_segment = closest_segment.rstrip(string.digits)
    
    if song_of_segment not in song_counts.keys():
        song_counts[song_of_segment] = 1
    else:
        song_counts[song_of_segment] += 1
        
    if song_counts[song_of_segment] > max_segments_per_song:
        not_first_blacklist = blacklist_query_addendum != ''
        if not_first_blacklist:
            blacklist_query_addendum += ' and '
        blacklist_query_addendum += 'name not like \'' + song_of_segment + '%\''

def retrieve_segment_from_corpus(corpus_path, closest_segment):
    video_segment = None
    while video_segment is None:
        try:
            video_segment = VideoFileClip(corpus_path + closest_segment + '.mp4')
        except BlockingIOError as e:
            print(e)
    
    return video_segment

def prepare_beat_frames(video_shift_seconds, audio, sample_rate, lr, hop_length):
    video_shift_frames = math.floor(video_shift_seconds * sample_rate / hop_length)
    beat_frames = extract_beat_frames(audio, sample_rate)
    beat_frames = beat_frames + video_shift_frames
    beat_frames[0] = max(0, beat_frames[0])
    duration = lr.get_duration(audio, sample_rate)
    final_frame = math.floor(duration * sample_rate / hop_length)
    beat_frames = np.append(beat_frames, final_frame)
    beat_count = []
    varied_beat_frames = vary_segment_lengths(beat_frames, beat_count)
    print(beat_count)
    return varied_beat_frames

def calc_audio_segment_duration(beat_times, video_segments_duration, start_time, i):
    if i == 0:
        audio_segment_duration = beat_times[i + 1] - start_time
    else:
        audio_segment_duration = beat_times[i + 1] - video_segments_duration
    return audio_segment_duration

def combine_video_segments_with_audio(audio_path, audio, concat_segments):
    audio = AudioFileClip(audio_path)
    audio = CompositeAudioClip([audio])
    concat_segments.audio = audio

def add_fx(audio_segment_duration, closest_segment, corresponding_video_segment, fx):
    scale_factor = corresponding_video_segment.duration / audio_segment_duration
    corresponding_video_segment = corresponding_video_segment.fx(vfx.speedx, scale_factor)
    
#     corresponding_video_segment = mp.video.fx.all.blackwhite(corresponding_video_segment)
        
    return corresponding_video_segment

def get_video_path(audio_path):
    last_slash_i = audio_path.rfind('/')
    second_last_slash_i = audio_path.rfind('/', 0, last_slash_i)
    video_path = audio_path[:second_last_slash_i + 1] + 'videos' + audio_path[last_slash_i:-4] + '.mp4'
    return video_path

def generate_music_video(audio_path,
                         video_settings,
                         running_with_ide=False):

    warnings.filterwarnings('ignore')
    
    video_shift_milliseconds = video_settings['audio_video_alignment']
    max_repeated_segments = video_settings['max_repeated_segments']
    
    NUM_MS_IN_SECONDS = 1000
    video_shift_seconds = video_shift_milliseconds/NUM_MS_IN_SECONDS
    
    # prepare audio
    corpus_path = '/Volumes/WD_BLACK/'
    audio, sample_rate = lr.load(audio_path, sr=None)

    window_length = round(.023 * sample_rate)  # 23ms window
    hop_length = round(window_length / 2)  # 50% overlap
    varied_beat_frames = prepare_beat_frames(video_shift_seconds, audio, sample_rate, lr, hop_length)
#     varied_beat_frames = varied_beat_frames[:5]
    beat_sample_cutoffs = segment_audio_by_beats(varied_beat_frames, hop_length)
    beat_times = lr.frames_to_time(varied_beat_frames, sr=sample_rate)
    
    segment_feature_vectors = get_segment_feature_vectors(beat_sample_cutoffs, audio, sample_rate)
    segment_feature_vectors = clean_feature_vectors(segment_feature_vectors)
    start = time.time()
    
    closest_segments = []
    video_segments = []
    video_segments_duration = 0
    start_time = beat_times[0]
    song_counts = {}
    blacklist_query_addendum = ''
    
    for i, segment_feature_vector in enumerate(segment_feature_vectors):
        print('Finding segment:', i)
        audio_segment_duration = calc_audio_segment_duration(beat_times, video_segments_duration, start_time, i)
        closest_segment = get_closest_segment(segment_feature_vector, 
                                              closest_segments, 
                                              audio_segment_duration, 
                                              blacklist_query_addendum,
                                              running_with_ide)
        
        closest_segments.append(closest_segment)
        
        blacklist_overused_song(max_repeated_segments, song_counts, blacklist_query_addendum, closest_segment)
        corresponding_video_segment = retrieve_segment_from_corpus(corpus_path, closest_segment)
        fx = {} #d once fx is initialized elsewhere
        corresponding_video_segment = add_fx(audio_segment_duration, 
                                             closest_segment, 
                                             corresponding_video_segment, 
                                             fx)
        
        
        video_segments.append(corresponding_video_segment)
        video_segments_duration += corresponding_video_segment.duration
        corresponding_video_segment.close()
    segment_selection_time = time.time()
    print('segment selection time:', segment_selection_time - start)

    concat_segments = concatenate_videoclips(video_segments, method='compose')
    combine_video_segments_with_audio(audio_path, audio, concat_segments)
    video_path = get_video_path(audio_path)
    concat_segments.write_videofile(video_path, codec='libx264', audio_codec='aac', audio_fps=sample_rate, preset='ultrafast')

#     os.remove(audio_path)

if __name__ == '__main__':
    from audio_similarity import flatten_features, generate_feature_stats, extract_features, get_closest_segment
    from segment_videos import extract_beat_frames, vary_segment_lengths

    start = time.time()
    video_settings = {'audio_video_alignment': 0, 'max_repeated_segments': 10}
    generate_music_video(audio_path='/Users/Nick/Desktop/misc/dj/posts/test.mp3', video_settings=video_settings,
                         running_with_ide=True)
    end = time.time()
    print('video generation time:', end - start)
else:
    from .audio_similarity import flatten_features, generate_feature_stats, extract_features, get_closest_segment
    from .segment_videos import extract_beat_frames, vary_segment_lengths
