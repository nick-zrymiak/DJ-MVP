import dataprep.connector
from dataprep.connector import connect
import asyncio
import moviepy.editor as mpe
import os
import pytube
import config
import urllib
import pandas as pd

def append_to_txt(path_name, text):
    with open(path_name, 'a') as file:
        file.write('%s\n' % text)

def remove_temporary_files(vid_path, audio_path):
    if os.path.exists(vid_path):
        os.remove(vid_path)
    if os.path.exists(audio_path):
        os.remove(audio_path)

def combine_audio_and_video(title, vid_path, audio_path):
    corpus_path = '/media/nick/WD_BLACK/corpus/'
    combined_vid_path = corpus_path + title
    command = 'ffmpeg -i "' + audio_path + '" -i "' + vid_path + '" -y -acodec copy -vcodec copy "' + combined_vid_path + '.mp4"'
    os.system(command)

def download_audio(audio_title, youtube):
    audio = youtube.streams.filter(only_audio=True).all()
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

def txt_to_list(file_path):
    new_list = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                currentPlace = line[:-1]  # removes linebreak
                new_list.append(currentPlace)

    return new_list

# YouTube search returns max 500 results per query. This limit is separate from API limits.
def get_video_data(query, num_videos=500):
    connector_path = './APIConnectors/api-connectors/'

    dc = connect(connector_path + 'youtube',
                 _auth={'access_token': config.api_key}, _concurrency=1)
                 
    videos = asyncio.run(dc.query(
        'videos',
        type='video',
        videoCategoryId='10',
        q=query,
        topicId='/m/02lkt',
        part='id, snippet',
        videoDuration='short',
        videoDefinition='high',
        _count=num_videos,
        ))

    return videos

def generate_query(word, prev_queried_words):
    new_query = 'edm official music video AND (intitle:"official video" OR intitle:"official music video")'
    
    for prev_queried_word in prev_queried_words:
        new_query += ' AND -intitle:"' + prev_queried_word + '"'
    
    new_query += ' AND intitle:"' + word + '"'
    
    return new_query

if __name__ == '__main__':
    prev_videos = './prev_downloaded_videos.txt'
    prev_downloaded_videos = txt_to_list(prev_videos)
    common_words_file = './common_words.txt'
    common_words = txt_to_list(common_words_file)
    prev_queried_words_file = './prev_queried_words.txt'
    prev_queried_words = txt_to_list(prev_queried_words_file)
    videos = pd.DataFrame()
    TARGET_NUM_VIDEOS = 10000
    current_queried_words = []
    '''
    try:
        # get_video_ids
        for i, word in enumerate(common_words):
            if len(videos) + len(prev_downloaded_videos) >= TARGET_NUM_VIDEOS:
                # remove_duplicates
                break
        
            if not word in prev_queried_words:            
                query = generate_query(word, prev_queried_words)
                
                # DataPrep query function fails if size of returned DataFrame is less than _count
                init_videos_size = len(videos)
                num_videos = 500
                while init_videos_size == len(videos):
                    try:
                        videos = videos.append(get_video_data(query, num_videos), ignore_index=True)
                    except ValueError:
                        num_videos -= 50
                
                prev_queried_words.append(word)
                current_queried_words.append(word)
    except dataprep.connector.errors.RequestError:
        print('API limit exceeded')
    finally:
        videos.to_csv('./current_videos.csv', index=False)
        
        for current_queried_word in current_queried_words:
            append_to_txt('./prev_queried_words.txt', current_queried_word)
    '''
    videos = pd.read_csv('./current_videos.csv')
    
    downloaded_videos = []
    for row in videos.iterrows():
        title = row[1]['title']
        title = title.lower()
        title = ''.join(c for c in title if c.isalnum() or c == ' ') # removes special characters
        is_music_video = 'official video' in title or 'official music video' in title
        
        if title in prev_downloaded_videos:
            print (title, 'has already been downloaded')
        elif is_music_video:
            url = 'https://www.youtube.com/watch?v=' + row[1]['videoId']
            youtube = pytube.YouTube(url)
            vid_path = './temp_files/' + title + '.mp4'
            audio_title = title + ' audio'
            audio_path = './temp_files/' + audio_title + '.mp4'
            
            try:
                streams = youtube.streams.all()
                highest_res, highest_res_id = get_best_stream(streams)
                
                if highest_res >= 1080:
                    download_visuals(title, youtube, highest_res_id)
                    audio_title = download_audio(audio_title, youtube)
                    
                    clip = mpe.VideoFileClip(vid_path)
                    audio = mpe.AudioFileClip(audio_path)

                    combine_audio_and_video(title, vid_path, audio_path)          
                    append_to_txt(prev_videos, title)
            except (ConnectionResetError, urllib.error.HTTPError, pytube.exceptions.LiveStreamError) as e:
                print(e)
            finally:
                remove_temporary_files(vid_path, audio_path)
                
