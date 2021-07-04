import librosa as lr
import subprocess
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def segment_video(unsegmented_video_path, video_name, video_path, beat_times):
    start_time = beat_times[0]
    for i, end_time in enumerate(beat_times[1:]):
        segment_path = unsegmented_video_path + '../segments/' + video_name[:-4] + str(i) + '.mp4'
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=segment_path)
        start_time = end_time

def extract_beat_times(audio_path):
    audio, sample_rate = lr.load(audio_path, sr=None)
    tempo, beats = lr.beat.beat_track(y=audio, sr=sample_rate)
    beat_times = lr.frames_to_time(beats, sr=sample_rate)
    return beat_times

def extract_audio(audio_path, video_path):
    command = 'ffmpeg -i ' + video_path + ' -ab copy -ac copy -ar copy -vn ' + audio_path
    subprocess.call(command, shell=True)

def append_to_txt(path_name, text):
    with open(path_name, 'a') as file:
        file.write('%s\n' % text)

def txt_to_list(file_path):
    new_list = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                currentPlace = line[:-1]  # removes linebreak
                new_list.append(currentPlace)

    return new_list

if __name__ == '__main__':
    unsegmented_video_path = '/media/nick/WD_BLACK/corpus/'
    video_names = [video_name for video_name in os.listdir(unsegmented_video_path) if video_name.endswith('.mp4')]
    prev_segmented_videos = txt_to_list('./segmented_videos.txt')
    video_names = [video_name for video_name in video_names if video_name not in prev_segmented_videos]

    for video_name in video_names:
        audio_path = './temp/' + video_name[:-4] + '.wav'
        video_path = unsegmented_video_path + video_name
        
        extract_audio(audio_path, video_path)
        beat_times = extract_beat_times(audio_path)
        segment_video(unsegmented_video_path, video_name, video_path, beat_times)
        append_to_txt('./segmented_videos.txt', video_name)
        os.remove(audio_path)
