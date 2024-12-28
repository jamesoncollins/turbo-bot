# main.py
from handlers.base_handler import BaseHandler

if __name__ == "__main__":
    handler_classes = BaseHandler.get_all_handlers()
    
    print(handler_classes)
    
    test_strings = [
        "Check this out: https://example.com",
        "Look here: https://another.com",
        "Visit us at https://examp.le",
        #"Here is a video: https://twitter.com/somepost",
        #"Check out this post: https://x.com/SaveUSAKitty/status/1872667773484363883",
        "#gpt write a haiuku",
        #"#gpt.image a flower",
        #"#gpt.gpt-4o-mini write a haiuku",
    ]

    for test_string in test_strings:
        print(f"\nProcessing test string: {test_string}")
        for handler_class in handler_classes:
            handler = handler_class(test_string)
            if handler.can_handle():
                print("Handler Used:", handler_class.get_name())
                print("Message:", handler.get_message())
                print("Attachments:", handler.get_attachments())

    print('Done')