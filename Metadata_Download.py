import os
import googleapiclient.discovery
import googleapiclient.errors
import requests
import json
import bs4
import pandas as pd
import openpyxl as xl
import datetime
from youtube_transcript_api import YouTubeTranscriptApi, formatters

import tkinter
import customtkinter

import threading # for multithreading

max_num_threads = 10 # max number of threads to run at once

API_Key = os.environ.get('YT_API_KEY')

def getChannelID(channel_url):
    """
    Given a YouTube channel URL, returns the channel ID and channel name.
    """
    
    try: 
        request = requests.get(channel_url)
        html = bs4.BeautifulSoup(request.text, 'html.parser')
        
        json_script = html.find("script", {"type": "application/ld+json"})
        channel_id = json.loads(json_script.text)['itemListElement'][0]['item']['@id'].split('/')[-1]
        channel_name = json.loads(json_script.text)['itemListElement'][0]['item']['name']
        return channel_id, channel_name
    except:
        return None, None

youtube = googleapiclient.discovery.build(
    "youtube", "v3", developerKey=API_Key)

def get_playlist(channel_id):
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    upload_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return upload_playlist_id

def get_playlist_items(playlist_id):
    
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=1
    )
    
    response = request.execute()
    videos = [response['items'][0]['contentDetails']['videoId']]
    
    total_video = response['pageInfo']['totalResults']
    counts = len(response['items'][0]['contentDetails']['videoId'])
    
    while 'nextPageToken' in response:
        nextPage = response['nextPageToken']
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPage
        )
        response = request.execute()
        counts += len(response['items'][0]['contentDetails']['videoId'])
        
        for i in range(len(response['items'])):
            videos.append(response['items'][i]['contentDetails']['videoId'])
        
    return videos

def get_video_metadata(video_id):
    
    video_meta_data = []
    
    for v_id in video_id:
        request = youtube.videos().list(
            part="snippet", 
            id=v_id
        )
        response = request.execute()
        video_meta_data.extend(response['items'])
        
    return video_meta_data

def process_video_metadata(video_metadata): # this function needs to be faster
    '''
    This function will process the video metadata and return a dictionary with the following keys:
    channel_id, video_id, descriptions, title, publishedAt, thumbnail
    '''
    
    # pd.set_option('display.max_columns', None)
    df = pd.DataFrame([], columns=['channel_id', 'video_id', 'video_description', 'video_title', 'video_publishedAt', 'video_thumbnail'])
    
    for metadata in video_metadata:
        channel_id = metadata['snippet']['channelId']
        video_id = metadata['id']
        video_publishedAt = datetime.datetime.strptime(metadata['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%m/%d/%Y')
        
        video_title = metadata['snippet']['title']
        video_description = metadata['snippet']['description']
        video_thumbnail = metadata['snippet']['thumbnails']['default']['url']

        response = {
            'channel_id': channel_id,
            'video_id': video_id,
            'video_description': None if video_description == " " else video_description,
            'video_title': video_title,
            'video_publishedAt': video_publishedAt, # convert to easy date format
            'video_thumbnail': video_thumbnail,
        }
        
        print('Processing video: ' + video_id + "\n\n\n")
        print(response)
        print("\n\n\n")
        
        temp_df = pd.DataFrame([response])
        df = pd.concat([df, temp_df], ignore_index=True)
    
    return df

def get_transcript(video_ids, pathToDir):
    
    srt_formatter = formatters.SRTFormatter()
    
    for id in video_ids:
        video_srt_transcript = None
        
        try:
            video_srt_transcript = srt_formatter.format_transcript(YouTubeTranscriptApi.get_transcript(id))
        except:
            pass
        
        if(video_srt_transcript == None):
            continue
        else:

            file_name = id + '.srt'
            full_path = os.path.join(pathToDir, file_name)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as file:
                # write with the video_id as the file name
                file.write(video_srt_transcript)

def process(url, path):
    '''
    This function will be called by the main script. It will call all the other functions in this file.
    '''
    
    print('Processing channel: ' + url + "\n\n\n")
    response = getChannelID(url)
    
    channel_id = response[0]
    channel_name = response[1]
    
    if(channel_id == None or channel_name == None):
        return '400 Bad Request'
    else: 
        print('Channel ID: ' + channel_id + "\n\n\n")
        print('Channel Name: ' + channel_name + "\n\n\n")
        
        playlist_id = get_playlist(channel_id)
        videos_ids = get_playlist_items(playlist_id)
        
        print('Number of videos: ' + str(len(videos_ids)) + "\n\n\n")
        
        video_metadata = get_video_metadata(videos_ids)
        
        print('Processing video metadata...\n\n\n')
        
        p_dataframe = process_video_metadata(video_metadata) # processed data is in excel format

        # # the directory named after the channel_name
        directory = f'{channel_name}/'
        
        # # write the excel folder to store the channel_name.xlsx file in
        if path[-1] != '/':
            path += '/'
            
        # # make sure that path has a '/' at the end
        if not os.path.exists(path + directory):
            os.makedirs(path + directory)
        
        # # write the excel file
        p_dataframe.to_excel(path + directory + channel_name + '.xlsx', index=False) # write the excel file to the path folder
        
        print('Finished writing excel file...\n\n\n')
        
        # calculate the number of threads to run
        num_threads = max(max_num_threads, min(max_num_threads, len(videos_ids)//50 + 1)) # 50 videos per thread)
        
        # split the videos_ids into num_threads lists with no overlap
        videos_ids_split = [videos_ids[i::num_threads] for i in range(num_threads)]
        
        # create a list of threads
        threads = []
        
        for i in range(num_threads):
            # create a thread
            thread = threading.Thread(target=get_transcript, args=(videos_ids_split[i], path + directory + 'transcripts/'))
            threads.append(thread)
            
            # start the thread
            thread.start()
            print('Started thread ' + str(i) + "\n\n\n")
            
        # wait for all threads to finish
        for thread in threads:
            thread.join() # wait for the thread to finish
            
        print('Finished processing transcripts...\n\n\n')
            
        return '200 OK' # return a status code of 200 OK
