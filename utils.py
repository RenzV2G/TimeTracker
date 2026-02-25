import re
import datetime

def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def get_current_timestamp():
    now = datetime.datetime.now()
    return {
        'date': now.strftime("%Y-%m-%d"),
        'time': now.strftime("%H:%M:%S"),
        'datetime': now,
        'formatted_time': now.strftime('%I:%M %p')
    }