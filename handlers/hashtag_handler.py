# handlers/hashtag_handler.py
from handlers.base_handler import BaseHandler
import re

class HashtagHandler(BaseHandler):

    is_intermediate = True  # Mark this as an intermediate class
     
    def __init__(self, input_str: str):
        super().__init__(input_str)
        self.hashtag_data = {}
        self.cleaned_input = input_str  # Initialize cleaned input

    def can_handle(self) -> bool:
        """
        Determines if the input string contains the specified hashtag followed by optional substrings.

        Returns:
            bool: True if the handler can process the input, False otherwise.
        """
        hashtag = self.get_hashtag()
        mapping = self.get_substring_mapping()
        self.hashtag_data = self.extract_hashtag(self.input_str, hashtag, mapping)
        
        if self.hashtag_data:
            self.cleaned_input = self.remove_hashtag(self.input_str, hashtag)
        print(self.hashtag_data)
        return bool(self.hashtag_data)

# handlers/base_handler.py
import importlib
import pkgutil
import inspect
import base64
import re
from urllib.parse import urlparse

class BaseHandler:
    def __init__(self, input_str: str):
        """
        Initialize the BaseHandler with an input string.

        Args:
            input_str (str): The input string to process.
        """
        self.input_str = input_str

    def can_handle(self) -> bool:
        """
        Determines if the handler can process the given string.

        Returns:
            bool: True if the handler can process the input, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_attachments(self) -> list:
        """
        Extracts attachments from the input string.

        Returns:
            list: A list of base64-encoded files.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_message(self) -> str:
        """
        Generates a reply message based on the input string.

        Returns:
            str: The generated reply message.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @staticmethod
    def get_name() -> str:
        """
        Returns the name of the handler.

        Returns:
            str: The name of the handler.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @staticmethod
    def get_all_handlers():
        handlers = []
        for _, module_name, _ in pkgutil.iter_modules(["handlers"]):
            module = importlib.import_module(f"handlers.{module_name}")
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseHandler) and obj is not BaseHandler and not getattr(obj, "is_intermediate", False):
                    handlers.append(obj)
        return handlers

    @staticmethod
    def file_to_base64(filename: str) -> str:
        """
        Converts a file to its base64-encoded representation.

        Args:
            filename (str): The path to the file.

        Returns:
            str: The base64-encoded content of the file.
        """
        with open(filename, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    @staticmethod
    def extract_url(input_str: str) -> str:
        """
        Extracts a URL from a larger string if one exists.

        Args:
            input_str (str): The input string to search.

        Returns:
            str: The first URL found, or an empty string if none exists.
        """
        match = re.search(r"https?://\S+", input_str)
        return match.group(0) if match else ""

    @staticmethod
    def is_url_in_domains(url: str, domains: list) -> bool:
        """
        Checks if a URL belongs to any of the specified domains.

        Args:
            url (str): The URL to check.
            domains (list): A list of allowed domains.

        Returns:
            bool: True if the URL is in the list of domains, False otherwise.
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(':')[0]  # Exclude port if present
        return domain in domains

# handlers/hashtag_handler.py
from handlers.base_handler import BaseHandler

class HashtagHandler(BaseHandler):
    is_intermediate = True  # Mark this as an intermediate class

    def __init__(self, input_str: str):
        super().__init__(input_str)
        self.hashtag_data = {}
        self.cleaned_input = input_str  # Initialize cleaned input

    def can_handle(self) -> bool:
        """
        Determines if the input string contains the specified hashtag followed by optional substrings.

        Returns:
            bool: True if the handler can process the input, False otherwise.
        """
        hashtag = self.get_hashtag()
        mapping = self.get_substring_mapping()
        self.hashtag_data = self.extract_hashtag(self.input_str, hashtag, mapping)

        if self.hashtag_data:
            self.cleaned_input = self.remove_hashtag(self.input_str, hashtag)

        return bool(self.hashtag_data)

    @staticmethod
    def extract_hashtag(input_str: str, hashtag: str, mapping: dict) -> dict:
        """
        Extracts the hashtag and its optional substrings into a dictionary. Defaults are used for missing substrings.

        Args:
            input_str (str): The input string to search.
            hashtag (str): The hashtag to search for.
            mapping (dict): A mapping of substring positions to keys and their defaults.

        Returns:
            dict: A dictionary containing the hashtag and its substrings.
        """
        pattern = fr"(?<!\w){re.escape(hashtag)}(?:\.[\w]+)*\b"
        #pattern = r"#\w+(\.\w+)*"
        match = re.search(pattern, input_str)

        substrings = match.group(0).split('.')[1:] if match else []
        result = {"hashtag": hashtag}

        for idx, (key, default) in mapping.items():
            result[key] = substrings[idx] if idx < len(substrings) else default

        if match:
            return result
            
        return None


    @staticmethod
    def remove_hashtag(input_str: str, hashtag: str) -> str:
        """
        Removes the hashtag and its substrings from the input string.

        Args:
            input_str (str): The input string.
            hashtag (str): The hashtag to remove.

        Returns:
            str: The input string without the hashtag and its substrings.
        """
        pattern = fr"\b{re.escape(hashtag)}(\.[\w]+)*\b"
        return re.sub(pattern, "", input_str).strip()

    def get_hashtag(self) -> str:
        """
        Provides the hashtag this handler is responsible for.

        Returns:
            str: The hashtag to look for.
        """
        raise NotImplementedError("Subclasses must implement get_hashtag method.")

    def get_substring_mapping(self) -> dict:
        """
        Provides the mapping of substring positions to keys.

        Returns:
            dict: A mapping of substring positions to dictionary keys.
        """
        raise NotImplementedError("Subclasses must implement get_substring_mapping method.")