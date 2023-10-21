import os
import googleapiclient.discovery
import googleapiclient.errors
import requests
import json
import bs4
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
    videos = response['items'][0]['contentDetails']['videoId']
    
    # while 'nextPageToken' in response:
    #     nextPage = response['nextPageToken']
    #     request = youtube.playlistItems().list(
    #         part="contentDetails",
    #         playlistId=playlist_id,
    #         maxResults=50,
    #         pageToken=nextPage
    #     )
    #     response = request.execute()
    #     videos.extend(response['items'])
        
    return videos

def get_video_metadata(video_id):
    request = youtube.videos().list(
        part="snippet", 
        id=video_id
    )
    response = request.execute()
    return response['items']

def video_snippet(video):
    return get_video_metadata(video)
        
def process():
    channel_id = getChannelID('https://www.youtube.com/@LehighU')
    playlist_id = get_playlist(channel_id)
    videos = get_playlist_items(playlist_id)
    video_metadata = video_snippet(videos)
    print(video_metadata)
    
process()
    
# transcript = YouTubeTranscriptApi.get_transcript('cD9bfxJE0K4')
# formatters = formatters.SRTFormatter()
# srt_transcript = formatters.format_transcript(transcript)
# channel_id, video_id, descriptions, title, 

# publishedAt, thumbnail