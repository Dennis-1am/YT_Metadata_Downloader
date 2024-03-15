import Metadata_Download
from tkinter import filedialog
import json

def number_of_api_calls_left():
    with open("lastModified.json", "r") as f:
        lines = f.readlines()
        json_data = json.loads(lines[0])
        return 10000 - json_data["total_api_calls"]
    
def last_modified():
    with open("lastModified.json", "r") as f:
        lines = f.readlines()
        json_data = json.loads(lines[0])
        return json_data["lastModified"]
    
exit_flag = False

while(not exit_flag):
    print("1. Download Metadata")
    print("2. API Calls Left")
    print("3. Exit")
    
    choice = input("Enter your choice: ")
    if choice == "1":
        print("Enter URL of the Channel: ")
        url = input()
        print("Select the folder to save the metadata: ")
        directory = filedialog.askdirectory()
        result = Metadata_Download.process(url, directory)
        if result == '400 Bad Request: API calls exceeded':
            print("-"*50)
            print("API calls exceeded. Try after some time.")
            print("-"*50)
            print("\n\n")
            continue
        elif result == '400 Bad Request':
            print("-"*50)
            print("Invalid URL. Try again.")
            print("-"*50)
            print("\n\n")
            continue
        print("\n\n")
        print("-"*50)
        print("Saved in ", directory)
        print("Channel URL: ", url)
        print("-"*50)
        print("\n\n")
    elif choice == "2":
        print("\n\n")
        print("-"*50)
        print("Last Modified: ", last_modified(), "\n")
        print("Total API Calls Left: ", number_of_api_calls_left(),)
        print("-"*50)
        print("\n\n")
    elif choice == "3":
        exit_flag = True
    else:
        print("Invalid choice")
        
