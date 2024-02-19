# check the storing data test folder and compare the transcript directory with the video directory
# print missing transcript files

import os
import json
import sys

def check(video_ids):
    video_dir = "/Users/dennis/Work Study/Youtube Data Project/YT_Metadata_Downloader/storing data test/Lehigh University College of Health/videos"
    transcript_dir = "/Users/dennis/Work Study/Youtube Data Project/YT_Metadata_Downloader/storing data test/Lehigh University College of Health/transcripts"
    video_files = os.listdir(video_dir)
    transcript = os.listdir(transcript_dir)
    missing = []
    
    for i in range(len(video_files)):
        video_files[i] = video_files[i].replace(".mp4", "")
        
    for i in range(len(transcript)):
        transcript[i] = transcript[i].replace(".srt", "")

    # compare the length of the two lists
    print("Length of video files: ", len(video_files))
    print("Length of transcript files: ", len(transcript))
    
    # print the missing files
    # check if transcript files has all the video_ids
    for i in range(len(video_ids)):
        if video_ids[i] not in transcript:
            missing.append(video_ids[i])
        if video_ids[i] not in video_files:
            missing.append(video_ids[i])
            
    print("Missing files: ", missing)
    
    return missing