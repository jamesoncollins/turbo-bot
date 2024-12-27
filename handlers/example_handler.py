# handlers/example_handler.py
from handlers.base_handler import BaseHandler

class ExampleHandler(BaseHandler):
    ALLOWED_DOMAINS = ["example.com", "examp.le"]

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        return url and self.is_url_in_domains(url, self.ALLOWED_DOMAINS)

    def get_attachments(self) -> list:
        return ["example_base64_attachment"]

    def get_message(self) -> str:
        return "Replying to a message with a URL for example.com or examp.le."

    @staticmethod
    def get_name() -> str:
        return "ExampleHandler"

# handlers/another_example_handler.py
from handlers.base_handler import BaseHandler

class AnotherExampleHandler(BaseHandler):
    ALLOWED_DOMAINS = ["another.com"]

    def can_handle(self) -> bool:
        url = self.extract_url(self.input_str)
        return url and self.is_url_in_domains(url, self.ALLOWED_DOMAINS)

    def get_attachments(self) -> list:
        return ["another_base64_attachment"]

    def get_message(self) -> str:
        return "Replying to a message with a URL for another.com."

    @staticmethod
    def get_name() -> str:
        return "AnotherExampleHandler"