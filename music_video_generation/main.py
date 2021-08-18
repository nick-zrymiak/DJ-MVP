import warnings
import os
from audio_similarity import *
from segment_videos import *
from moviepy.editor import *
import math

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

if __name__ == '__main__':
    video_shift_milliseconds = 0
    video_shift_seconds = video_shift_milliseconds/1000
    
    warnings.filterwarnings('ignore')
    audio_dir = '/Users/Nick/Desktop/misc/djmvp/audio/'
    corpus_path = '/Users/Nick/Desktop/misc/prev/corpus/WholeVideoCorpusStable20151207/'
    audio_name = [audio_name for audio_name in os.listdir(audio_dir) if not audio_name.startswith('.')]
    audio_name = audio_name[0]
    audio_path = audio_dir + audio_name
    audio, sample_rate = lr.load(audio_path, sr=None)
    
    hop_length = 512
    video_shift_frames = math.floor(video_shift_seconds*sample_rate/hop_length)
    beat_frames = extract_beat_frames(audio, sample_rate)
    beat_frames = beat_frames + video_shift_frames
    beat_frames[0] = max(0, beat_frames[0]) 
    
    duration = lr.get_duration(audio, sample_rate)
    final_frame = math.floor(duration*sample_rate/hop_length)
    beat_frames = np.append(beat_frames, final_frame)
    beat_count = []
    varied_beat_frames = vary_segment_lengths(beat_frames, beat_count) 
#     varied_beat_frames = varied_beat_frames[:5]
    print(beat_count)
    beat_sample_cutoffs = segment_audio_by_beats(varied_beat_frames, hop_length)
    beat_times = lr.frames_to_time(varied_beat_frames, sr=sample_rate)
    
    segmented_feature_vectors = get_segmented_feature_vectors(beat_sample_cutoffs, audio, sample_rate)
    segmented_feature_vectors = clean_feature_vectors(segmented_feature_vectors)
    
    closest_segments = []
    video_segments = []
    video_segments_duration = 0
    start_time = beat_times[0]
    for i, segmented_feature_vector in enumerate(segmented_feature_vectors):
        if i == 0:
            audio_segment_time = beat_times[i+1] - start_time
        else:
            audio_segment_time = beat_times[i+1] - video_segments_duration

        closest_segment = get_closest_segment(segmented_feature_vector, closest_segments, audio_segment_time)
        closest_segments.append(closest_segment)
        
        video_segment = None
        while video_segment is None:
            try:
                video_segment = VideoFileClip(corpus_path+closest_segment+'.mp4')
            except BlockingIOError as e:
                print(e)
        
        scale_factor = video_segment.duration/audio_segment_time
        print(closest_segment, scale_factor, video_segment.duration, audio_segment_time)
        video_segment = video_segment.fx(vfx.speedx, scale_factor)
        video_segments.append(video_segment)
        video_segments_duration += video_segment.duration
        
    concat_segments = concatenate_videoclips(video_segments, method='compose')
    audio = AudioFileClip(audio_path)
    audio = CompositeAudioClip([audio])
    concat_segments.audio = audio
    video_path = audio_dir + audio_name[:-4] + '.mp4'
    concat_segments.write_videofile(video_path, codec='libx264', audio_codec='aac', audio_fps=sample_rate, preset='ultrafast')
#     os.remove(audio_path) 
