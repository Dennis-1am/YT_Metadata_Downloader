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


API_Key = os.environ.get('YT_API_KEY')

def getChannelID(channel_url):
    """
    Given a YouTube channel URL, returns the channel ID.
    """
    request = requests.get(channel_url)
    html = bs4.BeautifulSoup(request.text, 'html.parser')
    
    json_script = html.find("script", {"type": "application/ld+json"})
    channel_id = json.loads(json_script.text)['itemListElement'][0]['item']['@id'].split('/')[-1]
    
    return channel_id

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
    
    total = response['pageInfo']['totalResults']
    counts = len(response['items'])
    
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
        
        # srt_formatter = formatters.SRTFormatter()
        
        # check if it has subtitles
        # video_srt_transcript = None
        # try :
        #     video_srt_transcript = { srt_formatter.format_transcript(YouTubeTranscriptApi.get_transcript(video_id)) }
        # except:
        #     pass
    
        
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
        # convert and write as we go to avoid memory issues with large datasets
        # convert to dataframe
        # temp_df = pd.DataFrame([response])
        # df = pd.concat([df, temp_df], ignore_index=True)
        # print(df)
        
    df.to_excel('metadata.xlsx', index=False)
    
    return df

def process():
    '''
    This function will be called by the main script. It will call all the other functions in this file.
    '''
    channel_id = getChannelID('https://www.youtube.com/@lehighcollegeofeducation2015')
    playlist_id = get_playlist(channel_id)
    videos = get_playlist_items(playlist_id)
    # print(videos)
    video_metadata = get_video_metadata(videos)
    # print(video_metadata)
    p_data = process_video_metadata(video_metadata)
    print(p_data)
    
process()