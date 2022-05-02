import librosa as lr
import subprocess
import os
import moviepy.editor as mp
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np
import math

def segment_video(unsegmented_video_path, video_name, video_path, beat_times, video_type):
    start_time = beat_times[0]
    
    for i, end_time in enumerate(beat_times[1:]):
        segment_path = '/Volumes/WD_BLACK/' + video_type + '_segments/' + video_name[:-4] + str(i) + '.mp4'
        with VideoFileClip(video_path) as video:
            clip = video.subclip(start_time, end_time)
            clip.write_videofile(segment_path, codec='libx264', audio_codec='aac', preset='ultrafast')
        start_time = end_time

def extract_beat_frames(audio, sample_rate, hop_length=512):
    _, beat_frames = lr.beat.beat_track(y=audio, sr=sample_rate, hop_length=hop_length)
    return beat_frames

def extract_beat_times(audio_path):
    audio, sample_rate = lr.load(audio_path, sr=None)
    beat_frames = extract_beat_frames(audio, sample_rate)
    beat_times = lr.frames_to_time(beat_frames, sr=sample_rate)
    return beat_times

def append_to_txt(path_name, text):
    with open(path_name, 'a') as file:
        file.write('%s\n' % text)

def txt_to_list(file_path):
    new_list = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                new_list = file.readlines()

    return new_list

def vary_segment_lengths(beat_times, beat_count=[]):
    varied_beat_times = [beat_times[0]]
    segment_beats = [1, 2, 4]
    candidate_segment_beats = []
    
    i = 0
    while True:
        candidate_segment_beats = [num_beats for num_beats in segment_beats if i % num_beats == 0]
        
        max_candidate = max(candidate_segment_beats)
        while i + max_candidate > len(beat_times):
            candidate_segment_beats.pop(-1)
            max_candidate = max(candidate_segment_beats)
        
        squared_beats = [beat**2 for beat in candidate_segment_beats]
        probabilities = [squared_beat/sum(squared_beats) for squared_beat in squared_beats]
        segment_length = np.random.choice(candidate_segment_beats, p=probabilities)
        
        i += segment_length
        if i == len(beat_times):
            if varied_beat_times[-1] != beat_times[-1]:
                varied_beat_times.append(beat_times[-1])
            break
        
        beat_count.append(segment_length)
        varied_beat_times.append(beat_times[i]) 
    
    return varied_beat_times

if __name__ == '__main__':
    video_type = 'medium_length_videos'
    unsegmented_video_path = '/Volumes/WD_BLACK/' + video_type + '/'
    video_names = [video_name for video_name in os.listdir(unsegmented_video_path) if video_name.endswith('.mp4') and not video_name.startswith('.')]
    video_names = sorted(video_names, key=str.lower)
    prev_segmented_videos = txt_to_list('./segmented_videos.txt')
    video_names = [video_name for video_name in video_names if video_name not in prev_segmented_videos]
    beat_count = []
    
    for video_name in video_names:
        video_path = unsegmented_video_path + video_name
        beat_times = extract_beat_times(video_path)
        segment_beat_times = vary_segment_lengths(beat_times, beat_count)
        segment_video(unsegmented_video_path, video_name, video_path, segment_beat_times, video_type)
        append_to_txt('./segmented_videos.txt', video_name)
        
        for beat in [1, 2, 4]:
            print('Segments of length ' + str(beat) + ' beats: ' + str(beat_count.count(beat)))
        print('\n')
        