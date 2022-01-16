import warnings
import os
from .audio_similarity import *
from .segment_videos import *
from moviepy.editor import *
import moviepy as mp
import math
import string

def segment_audio_by_beats(beat_frames, hop_length=512):
    beat_sample_cutoffs = [i * hop_length for i in beat_frames]
    return beat_sample_cutoffs

def get_segmented_feature_vectors(beat_sample_cutoffs, audio, sample_rate):
    segmented_feature_vectors = []
    for i, beat_sample_cutoff in enumerate(beat_sample_cutoffs):
        if i < len(beat_sample_cutoffs) - 1:
            print('beat:', i)
            beat_sample = audio[beat_sample_cutoff:beat_sample_cutoffs[i+1]]
            features = extract_features(audio=beat_sample, sample_rate=sample_rate)
            unflattened_stats = generate_feature_stats(features)
            stats = flatten_features(unflattened_stats)
            segmented_feature_vectors.append(stats)
        
    return segmented_feature_vectors

def clean_feature_vectors(segmented_feature_vectors):
    segmented_feature_vectors = pd.DataFrame(segmented_feature_vectors)
    segmented_feature_vectors = segmented_feature_vectors.fillna(segmented_feature_vectors.mean())
    return segmented_feature_vectors.values.tolist()

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

def get_hls_query_addendum(hue_min,
                           hue_max,
                           lightness_min, 
                           lightness_max,
                           saturation_min, 
                           saturation_max):
    
    return 'hue between ' + hue_min + ' and ' + hue_max + ' and ' \
            + 'lightness between ' + lightness_min + ' and ' + lightness_max + ' and ' \
            + 'saturation between ' + saturation_min + ' and ' + saturation_max

def add_fx(audio_segment_duration, closest_segment, corresponding_video_segment, fx):
    scale_factor = corresponding_video_segment.duration / audio_segment_duration
    corresponding_video_segment = corresponding_video_segment.fx(vfx.speedx, scale_factor)
    
    corresponding_video_segment = clip = mp.video.fx.all.blackwhite(corresponding_video_segment)
    corresponding_video_segment = clip = mp.video.fx.all.colorx(corresponding_video_segment, 2)
        
    return corresponding_video_segment


def get_video_path(audio_path):
    last_slash_i = audio_path.rfind('/')
    second_last_slash_i = audio_path.rfind('/', 0, last_slash_i)
    video_path = audio_path[:second_last_slash_i + 1] + 'videos' + audio_path[last_slash_i:-4] + '.mp4'
    return video_path

def generate_music_video(audio_path,
                         video_shift_milliseconds=0, 
                         max_segments_per_song=12, 
                         black_and_white=False,
                         colour_intensity=False,
                         hue_min='0', 
                         hue_max='255',
                         lightness_min='0', 
                         lightness_max='255',
                         saturation_min='0', 
                         saturation_max='255'):
    
    warnings.filterwarnings('ignore')
    
    MS_IN_SECONDS = 1000
    video_shift_seconds = video_shift_milliseconds/MS_IN_SECONDS
    
    # prepare audio
    corpus_path = '/Volumes/WD_BLACK/corpus_segments/'
    audio, sample_rate = lr.load(audio_path, sr=None)
    
    hop_length = 512
    varied_beat_frames = prepare_beat_frames(video_shift_seconds, audio, sample_rate, lr, hop_length)
#     varied_beat_frames = varied_beat_frames[:5]
    beat_sample_cutoffs = segment_audio_by_beats(varied_beat_frames, hop_length)
    beat_times = lr.frames_to_time(varied_beat_frames, sr=sample_rate)
    
    segmented_feature_vectors = get_segmented_feature_vectors(beat_sample_cutoffs, audio, sample_rate)
    segmented_feature_vectors = clean_feature_vectors(segmented_feature_vectors)
    
    closest_segments = []
    video_segments = []
    video_segments_duration = 0
    start_time = beat_times[0]
    song_counts = {}
    blacklist_query_addendum = ''
    hls_query_addendum = get_hls_query_addendum(hue_min, 
                                                hue_max,
                                                lightness_min, 
                                                lightness_max,
                                                saturation_min, 
                                                saturation_max)
    
#     fx = [fx for fx in [black_and_white, colour_intensity]] # make dict maybe
#     segment_fx = {}
#     for i in range(len(segmented_feature_vectors)):
#         segment_fx[str(i)] = 
    
    for i, segmented_feature_vector in enumerate(segmented_feature_vectors):
        audio_segment_duration = calc_audio_segment_duration(beat_times, video_segments_duration, start_time, i)
        closest_segment = get_closest_segment(segmented_feature_vector, 
                                              closest_segments, 
                                              audio_segment_duration, 
                                              blacklist_query_addendum,
                                              hls_query_addendum)
        
        closest_segments.append(closest_segment)
        
        blacklist_overused_song(max_segments_per_song, song_counts, blacklist_query_addendum, closest_segment)
        corresponding_video_segment = retrieve_segment_from_corpus(corpus_path, closest_segment)
#         corresponding_video_segment = add_fx(audio_segment_duration, 
#                                              closest_segment, 
#                                              corresponding_video_segment, 
#                                              fx)
        
        
        video_segments.append(corresponding_video_segment)
        video_segments_duration += corresponding_video_segment.duration
        
    concat_segments = concatenate_videoclips(video_segments, method='compose')
    combine_video_segments_with_audio(audio_path, audio, concat_segments)
    video_path = get_video_path(audio_path)
    concat_segments.write_videofile(video_path, codec='libx264', audio_codec='aac', audio_fps=sample_rate, preset='ultrafast')
#     os.remove(audio_path) 

if __name__ == '__main__':
    generate_music_video()
