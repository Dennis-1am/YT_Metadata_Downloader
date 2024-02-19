import os
import googleapiclient.discovery
import googleapiclient.errors
import requests
import json
import bs4
import pandas as pd
import json
import datetime
from youtube_transcript_api import YouTubeTranscriptApi, formatters
import yt_dlp
import threading # for multithreading
import check

max_num_threads = 10 # max number of threads to run at once

total_api_calls = 0 # total number of api calls made
max_api_calls = 10000 # max number of api calls allowed
API_Key = "AIzaSyBXSsKWzuL06jQGffwrF_kAI75WGd2y5Rg" # get the API key from the environment variables

def getChannelID(channel_url): # this function uses no api calls
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

def get_playlist(channel_id): # this function uses 1 api call per channel
    global total_api_calls  # Declare total_api_calls as a global variable
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    
    total_api_calls += 1
    
    upload_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return upload_playlist_id

def get_playlist_items(playlist_id): 
    global total_api_calls  # Declare total_api_calls as a global variable
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=1
    )
    total_api_calls += 1
    response = request.execute()
    videos = [response['items'][0]['contentDetails']['videoId']]
    
    total_video = response['pageInfo']['totalResults'] 
    
    if total_video > (max_api_calls - total_api_calls):
        return '400 Bad Request: API calls exceeded'
    
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
        total_api_calls += 1
        counts += len(response['items'][0]['contentDetails']['videoId'])
        
        for i in range(len(response['items'])):
            videos.append(response['items'][i]['contentDetails']['videoId'])
        
    return videos

def get_video_metadata(video_id):
    global total_api_calls  # Declare total_api_calls as a global variable
    video_meta_data = []
    
    for v_id in video_id:
        request = youtube.videos().list(
            part="snippet", 
            id=v_id
        )
        response = request.execute()
        video_meta_data.extend(response['items'])
        total_api_calls += 1
        
    return video_meta_data

def process_video_metadata(video_metadata): # this function needs to be faster
    '''
    This function will process the video metadata and return a dictionary with the following keys:
    channel_id, video_id, descriptions, title, publishedAt, thumbnail
    '''
    
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


def check_last_modified_date():
    '''
    This function will check the last modified date of the excel file and return the date
    '''
    global total_api_calls  # Declare total_api_calls as a global variable
    global max_api_calls # Declare max_api_calls as a global variable
    
    with open('lastModified.json', 'r') as file:
        lastModified = json.load(file)
    
    lastModified_Date = datetime.datetime.strptime(lastModified['lastModified'], '%Y-%m-%dT%H:%M:%SZ')
    current_Date = datetime.datetime.now()
    
    if((current_Date - lastModified_Date).days >= 1):
        lastModified['total_api_calls'] = 0
        total_api_calls = 0
        
        lastModified['lastModified'] = current_Date.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        total_api_calls = lastModified['total_api_calls']
        
    with open('lastModified.json', 'w') as file:
        json.dump(lastModified, file)
        
def save_last_count():
    '''
    This function will save the last count of the total_api_calls
    '''
    global total_api_calls  # Declare total_api_calls as a global variable
    
    with open('lastModified.json', 'r') as file:
        lastModified = json.load(file)
        
    lastModified['total_api_calls'] = total_api_calls
    
    with open('lastModified.json', 'w') as file:
        json.dump(lastModified, file)
        
def downloadVideo(video_ids, output_dir, 
                  format='best', 
                  ext='mp4'): 
    '''
        Download a youtube video using yt-dlp
    '''
        
    #print the path to the output directory
    print('Output directory: ' + output_dir + "\n\n\n")

    # create yt-dlp options
    ydl_opts = {
        'format': format,
        'outtmpl': os.path.join(output_dir, f'%(id)s.%(ext)s'),
        'quiet': False,
        'nooverwrites': False,
        'merge_output_format': ext,
        'external-downloader': 'ffmpeg',
    }

    # download the video
    if len(video_ids) > 1:
        for video_id in video_ids:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_id])
    else:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try :
                ydl.download(video_ids)
            except:
                print('Video not found: ' + video_ids[0] + "\n\n\n")
                return

    
def process(url, path):
    '''
    This function will be called by the main script. It will call all the other functions in this file.
    '''
    global total_api_calls  # Declare total_api_calls as a global variable
    global MAX_CALLS # Declare MAX_CALLS as a global variable
    
    check_last_modified_date() # check the last modified date of the excel file and reset the total_api_calls if necessary
    
    if(total_api_calls >= max_api_calls*0.8):
        return '400 Bad Request: API calls exceeded' 
    
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
        
        if(videos_ids == '400 Bad Request: API calls exceeded'):
            return '400 Bad Request: API calls exceeded'
        
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
            thread.start()
            print('Started thread ' + str(i) + "\n\n\n")
            
        # wait for all threads to finish
        for thread in threads:
            thread.join() # wait for the thread to finish
        
        
        download_threads = []
        total = 0
        for i in range(num_threads):
            # create a thread
            total += len(videos_ids_split[i])
            thread = threading.Thread(target=downloadVideo, args=(videos_ids_split[i], path + directory + 'videos/'))
            download_threads.append(thread)
            thread.start()
            print('Started download thread ' + str(i) + "\n\n\n")
        
        # wait for all threads to finish
        for thread in download_threads:
            thread.join()
            
        print('Total videos downloaded: ' + str(total) + "\n\n\n")
        
        print('Total API calls: ' + str(total_api_calls) + "\n\n\n")
    
        save_last_count() # save the last count of the total_api_calls
        
        missing = check.check(videos_ids) # check the storing data test folder and compare the transcript directory with the video directory
        
        if len(missing) > 1:
            print('Missing files: ' + str(missing[0]) + "\n\n\n")
            for missing_video in missing:
                print('Missing video: ' + missing_video + "\n\n\n")
                get_transcript([missing_video], path + directory + 'transcripts/')
                downloadVideo([missing_video], path + directory + 'videos/')
        elif len(missing) == 1:
            print('Missing video: ' + missing[0] + "\n\n\n")
            get_transcript([missing[0]], path + directory + 'transcripts/')
            downloadVideo([missing[0]], path + directory + 'videos/')
        
        if total_api_calls >= max_api_calls*0.7:
            return '200 OK: API CALLS LEFT: ' + str(max_api_calls - total_api_calls) + ' (API calls exceeded)'
        
        return '200 OK' # return a status code of 200 OK

# now: 0:03:20.947991 for 52 videos so 1 video takes 3.84 seconds
# start = datetime.datetime.now()
# print(process("https://www.youtube.com/@lehighuniversitycollegeofh8224", "/Users/dennis/Work Study/Youtube Data Project/YT_Metadata_Downloader/storing data test/"))
# end = datetime.datetime.now()
# print('Time taken: ' + str(end - start))

# get_transcript(['Ak7aQFtm7S0'], '/Users/dennis/Work Study/Youtube Data Project/YT_Metadata_Downloader/storing data test/Lehigh University College of Health/transcripts')