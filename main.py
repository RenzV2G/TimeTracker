import tkinter as tk
from tkinter import messagebox
import datetime
import threading
import time
import re
from pynput import mouse
import gspread
from google.oauth2.service_account import Credentials

# ================= GLOBALS =================
sheet = None
spreadsheet = None
last_activity = datetime.datetime.now()
is_clocked_in = False
current_row = None
current_activity = None
clock_in_time = None

IDLE_THRESHOLD = 360  # 6 minutes

# ================= GOOGLE AUTH =================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json", scopes=scope
)
client = gspread.authorize(creds)

# ================= SHEET FUNCTIONS =================

def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

def test_connection():
    global sheet, spreadsheet
    url = sheet_entry.get().strip()
    sheet_id = extract_sheet_id(url)

    if not sheet_id:
        messagebox.showerror("Error", "Invalid Google Sheets link.")
        return

    try:
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1
        messagebox.showinfo("Success", "Google Sheet connected successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Connection failed:\n{e}")

# ================= MOUSE TRACKING =================

def on_move(x, y):
    global last_activity
    last_activity = datetime.datetime.now()

mouse.Listener(on_move=on_move).start()

# ================= IDLE MONITOR =================

def monitor_idle():
    global current_activity

    while is_clocked_in:
        idle_seconds = (datetime.datetime.now() - last_activity).seconds

        if idle_seconds >= IDLE_THRESHOLD:
            if current_activity != "Idle":
                sheet.update(f"F{current_row}", "Idle")
                current_activity = "Idle"
        else:
            if current_activity != "Active":
                sheet.update(f"F{current_row}", "Active")
                current_activity = "Active"

        time.sleep(5)

# ================= CLOCK LOGIC =================

def clock_in():
    global is_clocked_in, current_row, clock_in_time, current_activity

    if not sheet:
        messagebox.showerror("Error", "Connect Google Sheet first.")
        return

    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Enter your name.")
        return

    now = datetime.datetime.now()
    clock_in_time = now
    is_clocked_in = True
    current_activity = "Active"

    row = [
        name,
        "Clocked In",
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S"),
        "",
        "Active"
    ]

    sheet.append_row(row)
    current_row = len(sheet.get_all_values())

    status_label.config(text="Status: Active")

    threading.Thread(target=monitor_idle, daemon=True).start()

def clock_out():
    global is_clocked_in

    if not is_clocked_in:
        return

    now = datetime.datetime.now()
    is_clocked_in = False

    duration = now - clock_in_time
    total_time = str(duration).split(".")[0]

    sheet.update(f"B{current_row}", "Clocked Out")
    sheet.update(f"D{current_row}", now.strftime("%H:%M:%S"))
    sheet.update(f"E{current_row}", total_time)
    sheet.update(f"F{current_row}", "Inactive")

    status_label.config(text="Status: Clocked Out")

# ================= GUI =================

root = tk.Tk()
root.title("Simple Team Time Tracker")
root.geometry("400x300")
root.resizable(False, False)

tk.Label(root, text="Google Sheets Link").pack(pady=5)
sheet_entry = tk.Entry(root, width=50)
sheet_entry.pack()

tk.Button(root, text="Test Connection", command=test_connection).pack(pady=5)

tk.Label(root, text="Enter Name").pack(pady=5)
name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="Clock In", command=clock_in).pack(pady=10)
tk.Button(root, text="Clock Out", command=clock_out).pack(pady=5)

status_label = tk.Label(root, text="Status: Not Clocked In")
status_label.pack(pady=20)

root.mainloop()