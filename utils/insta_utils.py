from instascrape import *
from insta_share import Instagram

    
def get_insta_sessionid():
    insta = Instagram()
    insta.login(os.environ["INSTA_USERNAME"], os.environ["INSTA_PASSWORD"])

    sessionid = insta.session["session_id"]
    return sessionid


def download_insta(url):
    newurl = url
    #newurl = url + "?utm_source=ig_web_button_share_sheet"
    #newurl = re.sub(r'/+', '/', newurl)
    print("Trying to download from " + newurl)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    fname = f"\\tmp\\reel\\file_{timestamp}.mp4"
    print("fname is " + fname)
    
    try:
        #SESSIONID = get_insta_sessionid()
        #headers = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.57",
        #       "cookie": f"sessionid={SESSIONID};"}
        msg_post = Reel(newurl)
        #msg_post.scrape(headers=headers)
        msg_post.scrape()
        msg_post.download(fp=fname)
    except Exception as ex:
        print(ex)
        return None
        
    return fname
    
    print('Downloaded Successfully.')