"""
setup_google_auth.py — Run this ONCE to authenticate with Google Calendar.

Usage:
    cd D:\AG\Widget
    python setup_google_auth.py

A browser window will open asking you to sign in and grant calendar access.
Once approved, token.json is saved and the widget picks it up automatically.
"""
import os, sys

CREDS = "credentials.json"
TOKEN = "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    # Check dependencies
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: Google libraries not installed.")
        print("Run:  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        sys.exit(1)

    # Check credentials file
    if not os.path.exists(CREDS):
        print(f"ERROR: {CREDS} not found in {os.getcwd()}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing existing token...")
            creds.refresh(Request())
        else:
            print("Opening browser for Google sign-in...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
        print(f"✓ Saved {TOKEN}")

    # Quick test — fetch today's events
    from googleapiclient.discovery import build
    import datetime
    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end   = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"
    result = service.events().list(
        calendarId="primary", timeMin=start, timeMax=end,
        singleEvents=True, orderBy="startTime"
    ).execute()
    items = result.get("items", [])
    print(f"\n✓ Connected! Found {len(items)} event(s) today:")
    for ev in items:
        t = ev["start"].get("dateTime", ev["start"].get("date", ""))[:16]
        print(f"  {t}  {ev.get('summary', '(no title)')}")
    if not items:
        print("  (calendar is empty today — that's fine)")
    print("\nAll done. Restart the widget app and the calendar widget will show live events.")

if __name__ == "__main__":
    main()
