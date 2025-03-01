# handlers/numberwang_handler.py
from handlers.hashtag_handler import HashtagHandler
from handlers.twitter_handler import download_video


class JafarHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#jafar"

    def get_substring_mapping(self) -> dict:
        return {0: ("ping", "pong")}

    def get_attachments(self) -> list:#todo maybe have a list of jafar videos and pick one at random, but have a way to specify?
        video_content = download_video("https://youtu.be/KI4-kzirdZo?si=PA4QS1GVMPq-_Ro2&t=4")
        if video_content:
            return [self.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("jafar") == "help":
            return self.get_help_text()
        return ""
        
    def get_help_text(self) -> str:
        return "Returns short clips of or pertaining to Jafar"

    @staticmethod
    def get_name() -> str:
        return "Jafar Handler"

class NumberwangHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#numberwang"

    def get_substring_mapping(self) -> dict:
        return {0: ("ping", "pong")}

    def get_attachments(self) -> list:
        video_content = download_video("https://youtu.be/0obMRztklqU")
        if video_content:
            return [self.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("numberwang") == "help":
            return self.get_help_text()
        return ""
        
    def get_help_text(self) -> str:
        return "That's numberwang!"

    @staticmethod
    def get_name() -> str:
        return "Numberwang Handler"