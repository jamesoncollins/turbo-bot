# handlers/base_handler.py
import importlib
import pkgutil
import inspect
import base64
import re
from urllib.parse import urlparse

class BaseHandler:
    def __init__(self, input_str: str, context = None):
        """
        Initialize the BaseHandler with an input string.

        Args:
            input_str (str): The input string to process.
        """
        self.input_str = input_str
        self.context = None

    def can_handle(self) -> bool:
        """
        Determines if the handler can process the given string.

        Returns:
            bool: True if the handler can process the input, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def process_message(self, msg, attachments):
        """Process a string and attachments.
        
        Args:
            input_str (str): The main input string.
            attachments (list): A list of Base64-encoded file strings.
        
        Returns:
            dict: A dictionary containing processed message and attachments.
        """
        # Generate the processed message and attachments
        processed_message = self.get_message()
        processed_attachments = self.get_attachments()
        
        return {
            "message": processed_message,
            "attachments": processed_attachments,
        }

    def assign_context(self, context):
        self.context = context

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
        Checks if a URL belongs to any of the specified domains or their subdomains.
    
        Args:
            url (str): The URL to check.
            domains (list): A list of allowed domains.
    
        Returns:
            bool: True if the URL is in the list of domains or their subdomains, False otherwise.
        """
        # Ensure the URL has a scheme; default to 'http://'
        if not urlparse(url).scheme:
            url = f"http://{url}"
    
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(':')[0]  # Exclude port if present
    
        # Check if the domain or its subdomains belong to the allowed domains
        for allowed_domain in domains:
            if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                return True
        return False


