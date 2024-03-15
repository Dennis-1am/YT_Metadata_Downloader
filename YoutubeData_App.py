import tkinter
from tkinter import filedialog

import customtkinter

import Metadata_Download as md


def submit_button_click():
   
    if(url == ""):
        status_label.configure(text="400 Bad Request", font=("Arial", 8, "bold"), text_color="red")
        status_label.update()
        return 0
    else:
        directory = filedialog.askdirectory()
        
        if directory == "":
            status_label.configure(text="400 Bad Request", font=("Arial", 8, "bold"), text_color="red")
            status_label.update()
            return 0
        
        s = md.process(url.get(), directory)
        
        if s == '200 OK':
            status_label.configure(text=s, font=("Arial", 8, "bold"), text_color="green")
            status_label.update()
            return 1
        else:
            status_label.configure(text=s, font=("Arial", 8, "bold"), text_color="red")
            status_label.update()
            return 0

app = customtkinter.CTk()
app.geometry("500x200")
app.maxsize(width=500, height=200)
app.title("Youtube Downloader")

app.eval('tk::PlaceWindow . center')

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# center the title status_label url link submit_button

title = customtkinter.CTkLabel(app, text="Insert a youtube channel link")
title.pack(padx=100, pady=10)

status_label = customtkinter.CTkLabel(app, text="Status of download")
status_label.pack()

url = tkinter.StringVar()
link = customtkinter.CTkEntry(app, width=350, height=40, corner_radius=15, textvariable=url)
link.pack( )

submit_button = customtkinter.CTkButton(app,
    text = "Submit", 
    command = lambda: submit_button_click()
)
submit_button.pack( pady=10 )

exit_button = customtkinter.CTkButton(app,
    text = "Exit", 
    command = lambda: app.destroy()
)
exit_button.pack( pady=10 )

app.mainloop()