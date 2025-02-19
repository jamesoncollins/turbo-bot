# handlers/numberwang_handler.py
from handlers.hashtag_handler import HashtagHandler

import requests

def get_impact_probability():
    url = "https://ssd-api.jpl.nasa.gov/sentry.api"
    params = {"des": "2024 YR4"}  # Query for asteroid 2024 YR4

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return f"API request failed with status code {response.status_code}"

    data = response.json()

    if "summary" not in data or "ip" not in data["summary"]:
        return "No impact probability data found for 2024 YR4"

    # Extract and convert the impact probability
    impact_probability_str = data["summary"]["ip"]  # Example: "0.031"
    impact_probability = float(impact_probability_str) * 100  # Convert to percentage

    return f"Impact Probability for 2024 YR4: {impact_probability:.2f}%"







class AsteroidHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#asteroid"

    def get_substring_mapping(self) -> dict:
        return {0: ("ping", "pong")}

    def get_attachments(self) -> list:
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("asteroid") == "help":
            return self.get_help_text()
        return get_impact_probability()
        
    def get_help_text(self) -> str:
        return "Returns probability of impact"

    @staticmethod
    def get_name() -> str:
        return "Asteroid Handler"

