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

        return bool(self.hashtag_data)

    @staticmethod
    def extract_hashtag(input_str: str, hashtag: str, mapping: dict) -> dict:
        """
        Extracts the hashtag and its optional substrings into a dictionary.

        Args:
            input_str (str): The input string to search.
            hashtag (str): The hashtag to search for.
            mapping (dict): A mapping of substring positions to keys.

        Returns:
            dict: A dictionary containing the hashtag and its substrings.
        """
        pattern = fr"\b{re.escape(hashtag)}(\.[\w]+)*\b"
        match = re.search(pattern, input_str)
        if match:
            substrings = match.group(0).split('.')[1:]
            result = {"hashtag": hashtag}
            for idx, substring in enumerate(substrings):
                key = mapping.get(idx, f"substring_{idx}")
                result[key] = substring
            return result
        return {}

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