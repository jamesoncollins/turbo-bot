# handlers/mmw_handler.py
from handlers.hashtag_handler import HashtagHandler
from utils import *
import os
from datetime import datetime

class mmwHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#mmw"

    def get_substring_mapping(self) -> dict:
        return {0: ("arg1", "arg1val")}

    def get_attachments(self) -> list:
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("arg1") == "help":
            return self.get_help_text()
        
        if self.context == None:
            raise Exception("need context")
        
        groupId_hashed = None
        try:
            groupId_hashed = hash_string(self.context.message.group)
        except:
            raise Exception("mmw only works for groups")

        msg = self.context.message.text
        sourceName = self.context.message.raw_message["envelope"]["sourceName"]
        sourceName = sourceName if sourceName else "Unknown"        
        sourceNumber = self.context.message.raw_message["envelope"]["sourceNumber"]
        sourceNumber = sourceNumber if sourceNumber else "Unknown"        
       
        fname = f"{groupId_hashed}/mmw.json"
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        if "#mmw" == msg:
            mmw = get_json_file_contents(fname, encryption_key=None)
            return "History: \n" + mmw            
        elif "#mmw" in msg:            
            mmw = sourceName + "(" + sourceNumber + "): " + msg
            append_to_json_file(
                fname, 
                {"sourceName": sourceName, "sourceNumber": sourceNumber, "time": datetime.now().isoformat(), "message": msg},
                encryption_key=None
                )
            return mmw
        
        raise Exception("shouldnt get here")
        
    @staticmethod    
    def get_help_text() -> str:
        return "mmw help:\nAdd #mmw to your message to save it on the log.\n Type #mmw alone to retrieve the log"

    @staticmethod
    def get_name() -> str:
        return "mmw Handler"
