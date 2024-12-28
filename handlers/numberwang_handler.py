# handlers/numberwang_handler.py
from handlers.hashtag_handler import HashtagHandler
from handlers.twitter_handler import TwitterHandler

class NumberwangHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#numberwang"

    def get_substring_mapping(self) -> dict:
        return {0: ("ping", "pong")}

    def get_attachments(self) -> list:
        return TwitterHandler.download_video(self,"https://youtu.be/0obMRztklqU")
        if video_content:
            return [BaseHandler.file_to_base64(video_content)]
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("model") == "help":
            return self.get_help_text()
        return ""
        
    def get_help_text(self) -> str:
        return "That's numberwang!"

    @staticmethod
    def get_name() -> str:
        return "Numberwang Handler"