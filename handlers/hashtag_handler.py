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
        hashtag_pattern = self.get_hashtag()
        mapping = self.get_substring_mapping()
        self.hashtag_data = self.extract_hashtag(self.input_str, hashtag_pattern, mapping)

        if self.hashtag_data:
            self.cleaned_input = self.remove_hashtag(self.input_str, hashtag_pattern)

        return bool(self.hashtag_data)

    @staticmethod
    def extract_hashtag(input_str: str, hashtag_pattern: str, mapping: dict) -> dict:
        """
        Extracts the hashtag and its optional substrings into a dictionary. Defaults are used for missing substrings.

        Args:
            input_str (str): The input string to search.
            hashtag_pattern (str): The regex pattern to search for the hashtag.
            mapping (dict): A mapping of substring positions to keys and their defaults.

        Returns:
            dict: A dictionary containing the hashtag and its substrings, or an empty dictionary if no match.
        """
        pattern = fr"(?<!\w){hashtag_pattern}((\.[^\.\s]+)*)\b"
        match = re.search(pattern, input_str)
        if not match:
            return {}

        matched_text = match.group(0)
        substrings = match.group(1).split('.')[1:] if match.group(1) else []
        result = {"hashtag": matched_text.split('.')[0]}

        for idx, (key, default) in mapping.items():
            result[key] = substrings[idx] if idx < len(substrings) else default

        return result


    @staticmethod
    def remove_hashtag(input_str: str, hashtag_pattern: str) -> str:
        """
        Removes the hashtag and its substrings from the input string.

        Args:
            input_str (str): The input string.
            hashtag_pattern (str): The regex pattern of the hashtag to remove.

        Returns:
            str: The input string without the hashtag and its substrings.
        """
        pattern = fr"(?<!\w){hashtag_pattern}(\.[\w]+)*\b"
        return re.sub(pattern, "", input_str).strip()

    def get_hashtag(self) -> str:
        """
        Provides the hashtag this handler is responsible for.

        Returns:
            str: The regex pattern for the hashtag to look for.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_substring_mapping(self) -> dict:
        """
        Provides the mapping of substring positions to keys and their defaults.

        Returns:
            dict: A mapping of substring positions to dictionary keys and defaults.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_help_text(self) -> str:
        """
        Provides help text explaining the purpose of substrings.

        Returns:
            str: A help message for the hashtag's substrings.
        """
        raise NotImplementedError("Subclasses must implement this method.")