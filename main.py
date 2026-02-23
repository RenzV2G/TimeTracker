import tkinter as tk
from tkinter import messagebox
import datetime
import threading
import time
import json
import re
import os

from pynput import mouse
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

IDLE_THRESHOLD = 360

# GLOBALS
sheet = None
creds = None
last_activity = datetime.datetime.now()
is_clocked_in = False
current_row = None
current_activity = "Active"
active_start_time = None
total_active_seconds = 0

# ================= OAUTH =================

def authenticate():
    global creds

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return gspread.authorize(creds)

# ================= UTIL =================

def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

def save_config(data):
    with open("config.json", "w") as f:
        json.dump(data, f)

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

# ================= IDLE MONITOR =================

def on_move(x, y):
    global last_activity
    last_activity = datetime.datetime.now()

mouse.Listener(on_move=on_move).start()

def monitor_idle():
    global current_activity, total_active_seconds, active_start_time

    while is_clocked_in:
        idle_time = (datetime.datetime.now() - last_activity).seconds

        if idle_time >= IDLE_THRESHOLD:
            if current_activity == "Active":
                total_active_seconds += (
                    datetime.datetime.now() - active_start_time
                ).seconds
                sheet.update(f"F{current_row}", "Idle")
                current_activity = "Idle"
                status_label.config(text="Status: Idle")
        else:
            if current_activity == "Idle":
                active_start_time = datetime.datetime.now()
                sheet.update(f"F{current_row}", "Active")
                current_activity = "Active"
                status_label.config(text="Status: Active")

        time.sleep(5)

# ================= APP =================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Freelance Time Tracker")
        self.geometry("400x300")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (SignInFrame, SheetFrame, UserFrame, DashboardFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(SignInFrame)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# ================= STEP 1 =================

class SignInFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Step 1: Sign in to Google", font=("Arial", 14)).pack(pady=20)

        tk.Button(self, text="Sign In with Google", width=25,
                  command=lambda: self.signin(controller)).pack()

    def signin(self, controller):
        try:
            authenticate()
            messagebox.showinfo("Success", "Signed in successfully!")
            controller.show_frame(SheetFrame)
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ================= STEP 2 =================

class SheetFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Step 2: Connect Sheet", font=("Arial", 14)).pack(pady=10)

        self.sheet_entry = tk.Entry(self, width=40)
        self.sheet_entry.pack(pady=5)
        self.sheet_entry.insert(0, "Paste Google Sheet Link")

        self.client_entry = tk.Entry(self, width=40)
        self.client_entry.pack(pady=5)
        self.client_entry.insert(0, "Client Name")

        tk.Button(self, text="Connect",
                  command=lambda: self.connect(controller)).pack(pady=10)

    def connect(self, controller):
        global sheet

        try:
            client = authenticate()
            sheet_id = extract_sheet_id(self.sheet_entry.get())
            sheet = client.open_by_key(sheet_id).sheet1

            config = load_config()
            config["client"] = self.client_entry.get()
            config["sheet_url"] = self.sheet_entry.get()
            save_config(config)

            messagebox.showinfo("Success", "Sheet Connected!")
            controller.show_frame(UserFrame)

        except Exception as e:
            messagebox.showerror("Error", str(e))

# ================= STEP 3 =================

class UserFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Step 3: Your Name", font=("Arial", 14)).pack(pady=20)

        self.name_entry = tk.Entry(self, width=30)
        self.name_entry.pack()

        config = load_config()
        if "name" in config:
            self.name_entry.insert(0, config["name"])

        tk.Button(self, text="Continue",
                  command=lambda: self.save_and_continue(controller)).pack(pady=15)

    def save_and_continue(self, controller):
        config = load_config()
        config["name"] = self.name_entry.get()
        save_config(config)
        controller.show_frame(DashboardFrame)

# ================= DASHBOARD =================

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        tk.Label(self, text="Dashboard", font=("Arial", 14)).pack(pady=10)

        tk.Button(self, text="Clock In", command=self.clock_in).pack(pady=5)
        tk.Button(self, text="Clock Out", command=self.clock_out).pack(pady=5)

        global status_label
        status_label = tk.Label(self, text="Status: Not Clocked In")
        status_label.pack(pady=10)

    def clock_in(self):
        global is_clocked_in, current_row
        global active_start_time, total_active_seconds

        config = load_config()
        name = config.get("name", "")
        client_name = config.get("client", "")

        now = datetime.datetime.now()

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

        is_clocked_in = True
        total_active_seconds = 0
        active_start_time = datetime.datetime.now()

        threading.Thread(target=monitor_idle, daemon=True).start()
        status_label.config(text="Status: Active")

    def clock_out(self):
        global is_clocked_in, total_active_seconds

        if not is_clocked_in:
            return

        now = datetime.datetime.now()

        if current_activity == "Active":
            total_active_seconds += (now - active_start_time).seconds

        h = total_active_seconds // 3600
        m = (total_active_seconds % 3600) // 60
        s = total_active_seconds % 60

        sheet.update(f"B{current_row}", "Clocked Out")
        sheet.update(f"D{current_row}", now.strftime("%H:%M:%S"))
        sheet.update(f"E{current_row}", f"{h:02}:{m:02}:{s:02}")
        sheet.update(f"F{current_row}", "Inactive")

        is_clocked_in = False
        status_label.config(text="Status: Clocked Out")

# ================= RUN =================

app = App()
app.mainloop()