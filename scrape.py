from dataprep.connector import connect
import asyncio
import moviepy.editor as mpe
import os
import pytube
import config

def store_vid_title(prev_videos, title):
    with open(prev_videos, 'a') as file:
        file.write('%s\n' % title)

def remove_temporary_files(vid_path, audio_path):
    os.remove(vid_path)
    os.remove(audio_path)

def combine_audio_and_video(title, vid_path, audio_path):
    corpus_path = '/media/nick/WD_BLACK/corpus/'
    combined_vid_path = corpus_path + title
    command = 'ffmpeg -i "' + audio_path + '" -i "' + vid_path + '" -y -acodec copy -vcodec copy "' + combined_vid_path + '.mp4"'
    os.system(command)

def download_audio(title, youtube):
    audio = youtube.streams.filter(only_audio=True).all()
    audio_title = title + ' audio'
    audio[0].download('./temp_files/', audio_title)
    return audio_title

def download_visuals(title, youtube, highest_res_id):
    video = youtube.streams.get_by_itag(highest_res_id)
    video.download('./temp_files/', title)

def get_best_stream(streams):
    highest_res = 0
    highest_res_id = None
    
    for stream in streams:
        resolution = stream.resolution
        if resolution != None:
            resolution = int(resolution[:-1])
            if resolution > highest_res and stream.mime_type == 'video/mp4' and 'avc1' in stream.video_codec:
                highest_res = resolution
                highest_res_id = stream.itag
    
    return highest_res, highest_res_id

def import_prev_downloaded_videos(prev_videos):
    prev_downloaded_videos = []
    if os.path.exists(prev_videos):
        with open(prev_videos, 'r') as file:
            for line in file:
                currentPlace = line[:-1]  # remove linebreak
                prev_downloaded_videos.append(currentPlace)

    return prev_downloaded_videos


def get_video_data(num_videos=10):
    connector_path = './APIConnectors/api-connectors/'

    dc = connect(connector_path + 'youtube',
                 _auth={'access_token': config.api_key}, _concurrency=1)
    videos = asyncio.run(dc.query(
        'videos',
        type='video',
        videoCategoryId='10',
        q='edm official music video',
        topicId='/m/02lkt',
        part='id, snippet',
        videoDuration='short',
        videoDefinition='high',
        _count=num_videos,
        ))

    return videos

if __name__ == '__main__':
    videos = get_video_data(5000)
    prev_videos = './prev_downloaded_videos.txt'
    prev_downloaded_videos = import_prev_downloaded_videos(prev_videos)
    
    downloaded_videos = []
    for row in videos.iterrows():
        title = row[1]['title']
        title = title.lower()
        title = ''.join(c for c in title if c.isalnum() or c == ' ') # remove special characters
        is_music_video = 'official video' in title or 'official music video' in title
        
        if title in prev_downloaded_videos:
            print (title, 'has already been downloaded')
        elif is_music_video:
            url = 'https://www.youtube.com/watch?v=' + row[1]['videoId']
            youtube = pytube.YouTube(url)
            streams = youtube.streams.all()
            highest_res, highest_res_id = get_best_stream(streams)
            
            if highest_res >= 1080:
                download_visuals(title, youtube, highest_res_id)
                audio_title = download_audio(title, youtube)

                vid_path = './temp_files/' + title + '.mp4'
                clip = mpe.VideoFileClip(vid_path)

                audio_path = './temp_files/' + audio_title + '.mp4'
                audio = mpe.AudioFileClip(audio_path)

                combine_audio_and_video(title, vid_path, audio_path)
                remove_temporary_files(vid_path, audio_path)
                
                store_vid_title(prev_videos, title)
