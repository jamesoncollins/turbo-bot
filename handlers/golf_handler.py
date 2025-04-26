# handlers/golf_handler.py
from handlers.hashtag_handler import HashtagHandler
from handlers.twitter_handler import download_video

class golfHandler(HashtagHandler):

    is_intermediate = False
    
    def get_hashtag(self) -> str:
        return r"#golf"

    def get_substring_mapping(self) -> dict:
        return {0: ("ping", "pong")}

    def get_attachments(self) -> list:
        return []

    def get_message(self) -> str:
        if self.hashtag_data.get("golf") == "help":
            return self.get_help_text()
        if self.cleaned_input == "":
            msg = "today"
        else:
            msg = self.cleaned_input
        parsed_date = dateparser.parse(msg, settings={'PREFER_DATES_FROM': 'future'})
        if not parsed_date:
            return "Invalid date input."
        
        date_to_check = parsed_date.strftime('%m-%d-%Y')
        try:
            session = requests.Session()
            logged_in = False
            tee_times = fetch_tee_times(session, date_to_check, logged_in)
            return get_tee_times_string(tee_times, date_to_check)
        
        except Exception as e:
            print(str(e))   
        
        return ""
        
    def get_help_text(self) -> str:
        return "That's golf!"

    @staticmethod
    def get_name() -> str:
        return "golf Handler"

import requests
import getpass
from datetime import datetime, timedelta
import dateparser

def pre_login_visit(session):
    url = 'https://foreupsoftware.com/index.php/booking/22236/10204'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }
    response = session.get(url, headers=headers)
    print("Pre-login visit status:", response.status_code)

def login(session, email, password):
    login_url = 'https://foreupsoftware.com/index.php/api/booking/users/login'
    payload = {
        'username': email,
        'password': password,
        'booking_class_id': '',
        'api_key': 'no_limits',
        'course_id': '22236'
    }
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Api-Key': 'no_limits',
        'Origin': 'https://foreupsoftware.com',
        'Referer': 'https://foreupsoftware.com/index.php/booking/22236/10204',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'X-Fu-Golfer-Location': 'foreup',
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = session.post(login_url, data=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get('logged_in'):
            print(f"Login successful for {data.get('first_name')} {data.get('last_name')}.")
            print("Relevant Account Info:")
            print(f"Email: {data.get('email')}")
            print(f"Phone: {data.get('cell_phone_number')}")
            print(f"Address: {data.get('address_1')}, {data.get('city')}, {data.get('state')} {data.get('zip')}")
            print(f"Membership: {data.get('member')}")
            print(f"Passes: {len(data.get('passes', {}))}")
            return True
        else:
            raise Exception(f"Login failed: {response.status_code}, {response.text}")
    else:
        raise Exception(f"Login failed: {response.status_code}, {response.text}")

def fetch_tee_times(session, date_str, logged_in):
    url = 'https://foreupsoftware.com/index.php/api/booking/times'
    booking_class = '13840' if logged_in else '13839'
    params = {
        'time': 'all',
        'date': date_str,  # Format: MM-DD-YYYY
        'holes': 'all',
        'players': '0',
        'booking_class': booking_class,
        'schedule_id': '10204',
        'schedule_ids[]': '10204',
        'specials_only': '0',
        'api_key': 'no_limits'
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Api-Key': 'no_limits',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Referer': 'https://foreupsoftware.com/index.php/booking/22236/10204#/teetimes',
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = session.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")

def get_tee_times_string(tee_times, date_to_check):
    result = f"Available tee times for {date_to_check}:\n"
    for slot in tee_times:
        time = slot['time']
        available_9 = slot['available_spots_9']
        available_18 = slot['available_spots_18']
        result += f"{time} - Available 9-hole: {available_9}, 18-hole: {available_18}\n"
    return result

if __name__ == "__main__":
    # Example usage
    use_login = input("Do you want to login? (yes/no): ").strip().lower()
    session = requests.Session()
    logged_in = False
    
    pre_login_visit(session)
    
    if use_login == 'yes':
        email = input("Enter your email: ")
        password = getpass.getpass("Enter your password: ")
        try:
            logged_in = login(session, email, password)
        except Exception as e:
            print(f"Login failed: {e}")
            exit()
    else:
        print("Proceeding without login...")
    
    user_input_date = input("Enter the date (e.g., '04-27-2025', 'tomorrow', 'Tuesday'): ").strip()
    parsed_date = dateparser.parse(user_input_date, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        print("Invalid date input.")
        exit()
    
    date_to_check = parsed_date.strftime('%m-%d-%Y')
    
    try:
        tee_times = fetch_tee_times(session, date_to_check, logged_in)
        print(f"Available tee times for {date_to_check}:")
    
        for slot in tee_times:
            time = slot['time']
            available_9 = slot['available_spots_9']
            available_18 = slot['available_spots_18']
            print(f"{time} - Available 9-hole: {available_9}, 18-hole: {available_18}")
    
    except Exception as e:
        print(str(e))
