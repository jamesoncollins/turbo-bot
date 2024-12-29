# handlers/mmw_handler.py
from handlers.hashtag_handler import HashtagHandler


from utils import print_file

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
        
        groupId = None
        try:
            groupId = self.context.message.group
            groupId = groupId.replace("/", "-")
        except:
            raise Exception("mmw only works for groups")

        msg = self.context.message.text
        sourceName = self.context.message.raw_message["envelope"]["sourceName"]
        sourceName = sourceName if sourceName else "Unknown"        
        sourceNumber = self.context.message.raw_message["envelope"]["sourceNumber"]
        sourceNumber = sourceNumber if sourceNumber else "Unknown"        
       
        if "#mmw" == msg:
            mmw = print_file(f"mmw{groupId}.txt")
            return "History: \n" + mmw            
        elif "#mmw" in msg:
            mmw = sourceName + "(" + sourceNumber + "): " + msg
            with open(f"mmw{groupId}.txt", "a") as file:
                file.write(mmw+"\n")
            return mmw
        
        raise Exception("shouldnt get here")
        
    def get_help_text(self) -> str:
        return "mmw help:\nAdd #mmw to your message to save it on the log.\n Type #mmw alone to retrieve the log"

    @staticmethod
    def get_name() -> str:
        return "mmw Handler"
