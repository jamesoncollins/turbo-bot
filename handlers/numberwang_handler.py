# handlers/numberwang_handler.py
from handlers.hashtag_handler import HashtagHandler

class GptHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#numberwang"

    def get_substring_mapping(self) -> dict:
        # Provide mapping and default value for 'model'
        return {0: ("numberwang", "https://youtu.be/0obMRztklqU")}

    def get_attachments(self) -> list:
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