import os.path
import datetime
from typing import List
from calendar_service import CalendarProvider, CalendarEvent

# Try imports, but don't fail hard if dependencies missing
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_DEPS_INSTALLED = True
except ImportError:
    GOOGLE_DEPS_INSTALLED = False

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class GoogleCalendarProvider(CalendarProvider):
    def __init__(self, credentials_path="credentials.json"):
        self.creds_path = credentials_path
        self.creds = None
        self.service = None
        
    def connect(self) -> bool:
        if not GOOGLE_DEPS_INSTALLED:
            print("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False

        if not os.path.exists(self.creds_path):
            print(f"Credentials file not found at {self.creds_path}")
            return False

        # Token exchange
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save token
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"Failed to build Google Service: {e}")
            return False

    def get_events(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[CalendarEvent]:
        if not self.service:
            if not self.connect():
                return []

        events_result = []
        try:
            # Google needs ISO format
            tmin = start_date.isoformat() + 'Z'
            tmax = end_date.isoformat() + 'Z' # Assumes UTC/Naive for simplicity or handle TZ
            
            calendar_list_entry = self.service.events().list(
                calendarId='primary', timeMin=tmin, timeMax=tmax,
                singleEvents=True, orderBy='startTime').execute()
            
            items = calendar_list_entry.get('items', [])
            
            for item in items:
                # Parse start/end
                start_str = item['start'].get('dateTime', item['start'].get('date'))
                end_str = item['end'].get('dateTime', item['end'].get('date'))
                
                # Simple parsing (naive)
                # In robust app, use dateutil.parser
                is_all_day = 'date' in item['start']
                
                # Populate object
                evt = CalendarEvent(
                    id=item['id'],
                    title=item.get('summary', 'No Title'),
                    start=datetime.datetime.now(), # Placeholder if parsing fails
                    end=datetime.datetime.now(),
                    description=item.get('description', ''),
                    location=item.get('location', ''),
                    is_all_day=is_all_day
                )
                events_result.append(evt)
                
        except Exception as e:
            print(f"Error fetching Google Events: {e}")
            
        return events_result

    def create_event(self, event: CalendarEvent) -> bool:
        # Not implemented yet for readonly
        return False
