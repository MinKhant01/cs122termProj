import datetime
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleCalendarEvent:
    def __init__(self, event):
        self.event = event

    def get_id(self):
        return self.event.get('id')

    def set_id(self, event_id):
        self.event['id'] = event_id

    def get_summary(self):
        return self.event.get('summary')

    def set_summary(self, summary):
        self.event['summary'] = summary

    def get_description(self):
        return self.event.get('description')

    def set_description(self, description):
        self.event['description'] = description

    def get_location(self):
        return self.event.get('location')

    def set_location(self, location):
        self.event['location'] = location

    def get_start_time(self):
        return self.event.get('start', {}).get('dateTime')

    def get_formatted_start_time(self):
        start_time = self.get_start_time()
        if start_time:
            dt = datetime.datetime.fromisoformat(start_time)
            return dt.strftime('%I:%M %p %Y-%m-%d')
        return None

    def set_start_time(self, start_time):
        if 'start' not in self.event:
            self.event['start'] = {}
        self.event['start']['dateTime'] = start_time

    def get_end_time(self):
        return self.event.get('end', {}).get('dateTime')

    def get_formatted_end_time(self):
        end_time = self.get_end_time()
        if end_time:
            dt = datetime.datetime.fromisoformat(end_time)
            return dt.strftime('%I:%M %p %Y-%m-%d')
        return None

    def set_end_time(self, end_time):
        if 'end' not in self.event:
            self.event['end'] = {}
        self.event['end']['dateTime'] = end_time

    def get_status(self):
        return self.event.get('status')

    def set_status(self, status):
        self.event['status'] = status

    def get_updated(self):
        return self.event.get('updated')

    def set_updated(self, updated):
        self.event['updated'] = updated

def get_google_calendar_events(user_email):
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    CLIENT_SECRET = os.getenv('GoogleClientSecret')
    TOKEN_FILE = f'token_{user_email}.json'
    client_config = {
        "installed": {
            "client_id": os.getenv('GoogleClientID'),
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }

    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            token_json = token.read()
            try:
                token_info = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                print("Loaded credentials from token file.")
            except json.JSONDecodeError:
                print("Failed to decode token JSON.")
                creds = None
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                print("Refreshed expired credentials.")
            else:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)
                print("Obtained new credentials via SSO.")
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
                print("Saved credentials to token file.")
        except Exception as e:
            print(f"Failed to obtain valid credentials: {e}")
            if 'invalid_grant' in str(e):
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                    print("Removed invalid token file. Please log in again.")
                return []
            return []

    service = build('calendar', 'v3', credentials=creds)

    local_tz = datetime.datetime.now().astimezone().tzinfo
    now = datetime.datetime.now(local_tz).isoformat()
    seven_days_later = (datetime.datetime.now(local_tz) + datetime.timedelta(days=7)).isoformat()

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          timeMax=seven_days_later, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return [GoogleCalendarEvent(event) for event in events]