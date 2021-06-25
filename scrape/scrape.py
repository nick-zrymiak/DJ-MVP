import dataprep.connector
from dataprep.connector import connect
import asyncio
import moviepy.editor as mpe
import os
import pytube
import config
import urllib
import pandas as pd
import csv
import datetime

def csv_to_dict(file_path):
    end_dates = {}
    
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        end_dates = {rows[0]:rows[1] for rows in reader}
        
    return end_dates

def get_video_ids(prev_downloaded_videos):
    prev_queried_dates = csv_to_dict('./prev_queried_dates.csv')
    end_dates_is_empty = not bool(prev_queried_dates)
    cur_time = datetime.datetime.utcnow()
    most_recent_date = cur_time
    earliest_date = cur_time
    date_range = 200
    
    if not end_dates_is_empty:
        most_recent_date = prev_queried_dates['most recent']
        earliest_date = prev_queried_dates['earliest']
        most_recent_date = datetime.datetime.strptime(most_recent_date, '%y/%m/%d %H:%M:%S')
        earliest_date = datetime.datetime.strptime(earliest_date, '%y/%m/%d %H:%M:%S')
    
    videos = pd.DataFrame()
    TARGET_NUM_VIDEOS = 10000
    min_date = earliest_date - datetime.timedelta(days=date_range)
    max_date = earliest_date
    
    try:
        while len(videos) + len(prev_downloaded_videos) < TARGET_NUM_VIDEOS:
            # DataPrep query function fails if size of returned DataFrame is less than _count
            init_videos_size = len(videos)
            while init_videos_size == len(videos):
                try:
                    videos = videos.append(get_video_data(min_date, max_date), ignore_index=True)
                except ValueError:
                    delta_range = 100
                    date_range += delta_range
                    min_date -= datetime.timedelta(days=delta_range)       
            earliest_date = min_date
            min_date -= datetime.timedelta(days=date_range)
            max_date -= datetime.timedelta(days=date_range)
    except dataprep.connector.errors.RequestError as e:
        print(e)
    finally:
        print('date_range:', date_range)
        videos.to_csv('./current_videos.csv', index=False)
        
        prev_queried_dates['earliest'] = earliest_date
        prev_queried_dates['most recent'] = most_recent_date
        
        with open('./prev_queried_dates.csv', 'w') as file:
            for key in prev_queried_dates.keys():
                datetime_obj = prev_queried_dates[key]
                file.write("%s,%s\n"%(key, datetime_obj.strftime('%y/%m/%d %H:%M:%S')))
    
    return videos

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
def get_video_data(min_date, max_date, num_videos=400):
    connector_path = './APIConnectors/api-connectors/'

    dc = connect(connector_path + 'youtube',
                 _auth={'access_token': config.api_key}, _concurrency=1)
    
    min_date = min_date.isoformat('T') + 'Z'
    max_date = max_date.isoformat('T') + 'Z'
                 
    videos = asyncio.run(dc.query(
        'videos',
        type='video',
        q='edm official music video',
        part='id, snippet',
        videoDuration='short',
        videoDefinition='high',
        publishedAfter=min_date,
        publishedBefore=max_date,
        _count=num_videos,
        ))

    return videos

if __name__ == '__main__':
    prev_videos = './prev_downloaded_videos.txt'
    prev_downloaded_videos = txt_to_list(prev_videos)
#     videos = get_video_ids(prev_downloaded_videos)
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
                
