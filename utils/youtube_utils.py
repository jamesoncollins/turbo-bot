from pytubefix import YouTube

def download_youtube_video(link):
    # where to save 
    SAVE_PATH = "./"

    try: 
        # object creation using YouTube 
        yt = YouTube(link) 
        ys = yt.streams.get_highest_resolution()        
        ys.download(filename="youtube.mp4", output_path=SAVE_PATH)
        print('Video downloaded successfully!')        
    except Exception as ex:
        print(ex)
        return None    
        
    return SAVE_PATH + "/youtube.mp4"

def is_youtube_domain(msg):
    if "youtube.com" in msg:
        print("is youtube url")
        return extract_url(msg, "youtube.com")
    if "youtu.be" in msg:
        print("is youtube url")
        return extract_url(msg, "youtu.be")
    else:
        return None