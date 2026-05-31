import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'
TOKEN_FILE = BASE_DIR / 'token.json'


def get_calendar_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(str(TOKEN_FILE), 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


def create_watering_event(plant_name, watering_date, calendar_id='primary'):
    try:
        service = get_calendar_service()
        event = {
            'summary': f'🌿 {plant_name} 물주기',
            'description': f'{plant_name} 화분에 물을 주세요! 🪴',
            'start': {
                'date': watering_date.strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'date': watering_date.strftime('%Y-%m-%d'),
                'timeZone': 'Asia/Seoul',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440}, # D-1 알람 설정 (1440분 = 24시간)
                ],
            },
        }
        created_event = service.events().insert(
            calendarId=calendar_id, body=event
        ).execute()
        return created_event.get('id')
    except Exception as e:
        print(f'캘린더 이벤트 생성 오류: {e}')
        return None


def delete_event(event_id, calendar_id='primary'):
    try:
        service = get_calendar_service()
        service.events().delete(
            calendarId=calendar_id, eventId=event_id
        ).execute()
        return True
    except Exception as e:
        print(f'캘린더 이벤트 삭제 오류: {e}')
        return False


def update_watering_event(event_id, plant_name, new_date, calendar_id='primary'):
    try:
        # 기존 이벤트 삭제하고 재생성
        if event_id:
            delete_event(event_id, calendar_id)
        return create_watering_event(plant_name, new_date, calendar_id)
    except Exception as e:
        print(f'캘린더 이벤트 수정 오류: {e}')
        return None
