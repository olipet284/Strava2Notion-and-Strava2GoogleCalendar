from stravalib.client import Client
from datetime import timedelta, datetime
import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import utils
from dotenv import load_dotenv
import os

load_dotenv()

# ------------------
# --- Strava API ---
# ------------------

strava_client_id = os.getenv("strava_client_id")
strava_client_secret = os.getenv("strava_client_secret")

# Open the following link
print(
    f"http://www.strava.com/oauth/authorize?client_id={strava_client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all"
)
# And obtain
# http://localhost/exchange_token?state=&code={strava_code}&scope=read,activity:read_all

strava_code = None

# Add the access token printet in the first run, so you don't have to autherize and copy the strava_code again.
access_token = None

if not access_token:
    token_dict = Client().exchange_code_for_token(
        client_id=strava_client_id, client_secret=strava_client_secret, code=strava_code
    )
    access_token = token_dict["access_token"]
    print(f"{access_token = }")

StravaClient = Client(access_token=access_token)

activities = StravaClient.get_activities(before=datetime.now(), limit=500)

# ---------------------------
# --- Google Calendar API ---
# ---------------------------

calendarId = os.getenv("calendarId")

# The following is code from https://developers.google.com/people/quickstart/python
# Here you can also change some code a bit to get the desired calendarId
# Here you also find information on how to create the credentials.json file

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("calendar", "v3", credentials=creds)

# ------------------
# --- Notion API ---
# ------------------

NotionToken = os.getenv("NotionToken")
DatabaseId = os.getenv("DatabaseId")

headers = {
    "Authorization": "Bearer " + NotionToken,
    "Content-Type": "application/json",
    # Check what is the latest version here: https://developers.notion.com/reference/changes-by-version
    "Notion-Version": "2022-06-28",
}

# Run the following command in order to get the table format of the pages in the
# database and how to change the create_page() function for you specific database
utils.example_page_format(DatabaseId, headers)


for activity in activities:
    title = activity.name
    description = activity.description
    strava_id = activity.id
    moving_time = activity.moving_time.seconds
    elapsed_time = activity.elapsed_time
    elevation = int(activity.total_elevation_gain)
    distance = int(activity.distance)
    activity_type = activity.type
    start_date_google_cal = activity.start_date
    end_date_google_cal = start_date_google_cal + elapsed_time
    start_date_notion = activity.start_date + timedelta(hours=2)
    end_date_notion = start_date_notion + elapsed_time
    # Quick fix in the start_notion and end_notion dates (specific to my timezone)
    date = {
        "start_google_cal": start_date_google_cal.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_google_cal": end_date_google_cal.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_notion": f'{start_date_notion.strftime("%Y-%m-%dT%H:%M:%S")}.000+02:00',
        "end_notion": f'{end_date_notion.strftime("%Y-%m-%dT%H:%M:%S")}.000+02:00',
    }

    cover_url = None
    # The following is how I thought you might be able to add the
    # picture from Strava as the cover in Notion, but I was wrong

    # if activity.total_photo_count != 0:
    #    if activity.:
    #        cover_url = activity.photos.primary.urls["600"]

    if activity_type == "Hike":
        icon = "🥾"
    elif activity_type == "Ride":
        icon = "🚲"
    elif activity_type == "Run":
        icon = "👟"
    elif activity_type == "WeightTraining":
        icon = "🏋🏻‍♂️"
    elif activity_type == "Yoga":
        icon = "🧘🏻‍♂️"
    else:
        icon = "🔴"

    # ------------------------------
    # --- Google Calendar Upload ---
    # ------------------------------

    body = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": date["start_google_cal"],
            "timeZone": "Europe/Berlin",
        },
        "end": {
            "dateTime": date["end_google_cal"],
            "timeZone": "Europe/Berlin",
        },
    }

    service.events().insert(calendarId=calendarId, body=body).execute()

    # ---------------------
    # --- Notion Upload ---
    # ---------------------

    data = utils.table_scheme(
        date, activity_type, distance, moving_time, elevation, strava_id, title
    )

    if utils.create_page(headers, DatabaseId, data, icon, cover_url) is None:
        break
