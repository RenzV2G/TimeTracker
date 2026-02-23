import tkinter as tk
from tkinter import ttk, messagebox
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


# ================= CONFIG =================

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {"clients": {}}


def save_config(data):
    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)


def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None


# ================= MAIN APP =================

class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Freelance Time Tracker")
        self.geometry("560x520")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.configure(bg="#f4f6f9")
        self.style.configure("TFrame", background="#f4f6f9")
        self.style.configure("TLabel", background="#f4f6f9", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Primary.TButton",
                     font=("Segoe UI", 10, "bold"),
                     padding=6)
        self.style.configure("Treeview",
                     font=("Segoe UI", 10),
                     rowheight=28)
        self.style.configure("Treeview.Heading",
                     font=("Segoe UI", 10, "bold"))

        self.config_data = load_config()

        self.sheet = None
        self.current_client = None
        self.is_clocked_in = False
        self.current_row = None
        self.active_start = None
        self.total_active = 0
        self.last_activity = datetime.datetime.now()
        self.current_activity = "Active"

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=30, pady=20)

        self.frames = {}

        for F in (SignInFrame, NameFrame, SheetFrame, DashboardFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.auto_navigate()
        mouse.Listener(on_move=self.on_move).start()

    # ---------- AUTH ----------

    def is_logged_in(self):
        return os.path.exists("token.json")

    def authenticate(self):
        creds = None

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

    def sign_out(self):
        if os.path.exists("token.json"):
            os.remove("token.json")
        self.config_data = load_config()
        self.auto_navigate()

    # ---------- NAVIGATION ----------

    def auto_navigate(self):
        if not self.is_logged_in():
            self.show_frame(SignInFrame)
        elif not self.config_data.get("name"):
            self.show_frame(NameFrame)
        else:
            self.show_frame(DashboardFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, "refresh"):
            frame.refresh()

    # ---------- IDLE ----------

    def on_move(self, x, y):
        self.last_activity = datetime.datetime.now()

    def monitor_idle(self):
        while self.is_clocked_in:
            idle_time = (datetime.datetime.now() - self.last_activity).seconds

            if idle_time >= IDLE_THRESHOLD:
                if self.current_activity == "Active":
                    self.total_active += (
                        datetime.datetime.now() - self.active_start
                    ).seconds
                    self.sheet.update(f"F{self.current_row}", "Idle")
                    self.current_activity = "Idle"
            else:
                if self.current_activity == "Idle":
                    self.active_start = datetime.datetime.now()
                    self.sheet.update(f"F{self.current_row}", "Active")
                    self.current_activity = "Active"

            time.sleep(5)
    
    def get_first_empty_row(self):
        data = self.sheet.get_all_values()

        for i, row in enumerate(data, start=1):
            if not any(cell.strip() for cell in row):
                return i

        return len(data) + 1


# ================= SIGN IN =================

class SignInFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        ttk.Label(self, text="Sign in to Google", font=("Segoe UI", 18)).pack(pady=80)
        ttk.Button(self, text="Sign In", command=lambda: self.login(app)).pack()

    def login(self, app):
        try:
            app.authenticate()
            app.auto_navigate()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ================= NAME =================

class NameFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        ttk.Label(self, text="Enter Your Name", font=("Segoe UI", 18)).pack(pady=80)

        self.entry = ttk.Entry(self, width=30)
        self.entry.pack()

        ttk.Button(self, text="Save", command=lambda: self.save(app)).pack(pady=20)

    def refresh(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, load_config().get("name", ""))

    def save(self, app):
        app.config_data["name"] = self.entry.get()
        save_config(app.config_data)
        app.auto_navigate()


# ================= SHEETS =================

class SheetFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self,
                  text="Manage Client Sheets",
                  style="Header.TLabel").pack(pady=15)

        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Client", "SheetID"),
            show="headings",
            height=8
        )

        self.tree.heading("Client", text="Client")
        self.tree.heading("SheetID", text="Sheet ID")

        self.tree.column("Client", width=180, anchor="center")
        self.tree.column("SheetID", width=260, anchor="center")

        self.tree.pack()

        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10)

        self.edit_btn = ttk.Button(
            action_frame,
            text="✏ Edit",
            command=self.edit_selected,
            style="Primary.TButton"
        )
        self.edit_btn.pack(side="left", padx=10)

        self.delete_btn = ttk.Button(
            action_frame,
            text="🗑 Delete",
            command=self.delete_selected,
            style="Primary.TButton"
        )
        self.delete_btn.pack(side="left", padx=10)

        ttk.Button(self,
                   text="Add New Client",
                   command=self.add_popup,
                   style="Primary.TButton").pack(pady=5)

        ttk.Button(self,
                   text="Back to Dashboard",
                   command=lambda: app.show_frame(DashboardFrame)).pack(pady=5)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())

        config = load_config()
        for name, data in config.get("clients", {}).items():
            self.tree.insert(
                "",
                "end",
                values=(name, data["sheet_id"])
            )

    def get_selected_client(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Client", "Please select a client.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def edit_selected(self):
        client = self.get_selected_client()
        if client:
            self.edit_popup(client)

    def delete_selected(self):
        client = self.get_selected_client()
        if not client:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{client}'?"
        )
        if confirm:
            config = load_config()
            del config["clients"][client]
            save_config(config)
            self.refresh()

    def add_popup(self):
        self.edit_popup()

    def edit_popup(self, client_name=None):
        popup = tk.Toplevel(self)
        popup.title("Client Setup")
        popup.geometry("400x250")
        popup.configure(bg="#f4f6f9")

        ttk.Label(popup, text="Client Name").pack(pady=5)
        name_entry = ttk.Entry(popup, width=40)
        name_entry.pack()

        ttk.Label(popup, text="Google Sheet URL").pack(pady=5)
        url_entry = ttk.Entry(popup, width=40)
        url_entry.pack()

        if client_name:
            config = load_config()
            data = config["clients"][client_name]
            name_entry.insert(0, client_name)
            url_entry.insert(0, data["sheet_url"])

        def save():
            try:
                sheet_id = extract_sheet_id(url_entry.get())
                if not sheet_id:
                    raise Exception("Invalid Google Sheets URL.")

                client = self.app.authenticate()
                sheet = client.open_by_key(sheet_id).sheet1
                _ = sheet.row_count

                config = load_config()
                config["clients"][name_entry.get()] = {
                    "sheet_url": url_entry.get(),
                    "sheet_id": sheet_id
                }

                if client_name and client_name != name_entry.get():
                    del config["clients"][client_name]

                save_config(config)
                popup.destroy()
                self.refresh()

            except Exception as e:
                messagebox.showerror("Connection Error", str(e))

        ttk.Button(popup,
                   text="Save",
                   command=save,
                   style="Primary.TButton").pack(pady=15)


# ================= DASHBOARD =================

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Label(header,
                  text="Dashboard",
                  style="Header.TLabel").pack(side="left")

        settings_btn = ttk.Menubutton(header, text="⚙")
        menu = tk.Menu(settings_btn, tearoff=0)
        menu.add_command(label="Edit Name",
                         command=lambda: app.show_frame(NameFrame))
        menu.add_command(label="Sign Out", command=app.sign_out)
        settings_btn["menu"] = menu
        settings_btn.pack(side="right")

        ttk.Separator(self).pack(fill="x", pady=10)

        self.greeting = ttk.Label(self, font=("Segoe UI", 13))
        self.greeting.pack(pady=5)

        row = ttk.Frame(self)
        row.pack()

        self.client_var = tk.StringVar()

        self.client_dropdown = ttk.Combobox(
            row,
            textvariable=self.client_var,
            state="readonly",
            width=28
        )
        self.client_dropdown.pack(side="left")

        self.client_dropdown.bind("<<ComboboxSelected>>", self.load_client)

        self.status_icon = tk.Label(row, text="⚪", font=("Segoe UI", 14),
                                    bg="#f4f6f9")
        self.status_icon.pack(side="left", padx=5)

        ttk.Button(self,
                   text="Sheets",
                   command=lambda: app.show_frame(SheetFrame),
                   style="Primary.TButton").pack(pady=5)

        ttk.Separator(self).pack(fill="x", pady=10)

        self.status_label = ttk.Label(self, text="Not Clocked In")
        self.status_label.pack()

        self.timestamp_label = ttk.Label(self, text="Last Action: --")
        self.timestamp_label.pack()

        self.total_label = ttk.Label(self,
                                     text="00:00:00",
                                     font=("Segoe UI", 22, "bold"))
        self.total_label.pack(pady=15)

        self.clock_in_btn = ttk.Button(self,
                                       text="Clock In",
                                       command=self.clock_in,
                                       style="Primary.TButton")

        self.clock_out_btn = ttk.Button(self,
                                        text="Clock Out",
                                        command=self.clock_out,
                                        style="Primary.TButton")

        self.clock_in_btn.pack(pady=10)

    def refresh(self):
        config = load_config()
        self.greeting.config(text=f"Hello, {config.get('name','')} 👋")

        clients = list(config.get("clients", {}).keys())
        self.client_dropdown["values"] = clients

    def load_client(self, event=None):
        self.status_icon.config(text="🟡")

        config = load_config()
        client_name = self.client_var.get()
        client_data = config["clients"].get(client_name)

        try:
            client = self.app.authenticate()
            sheet = client.open_by_key(client_data["sheet_id"]).sheet1
            _ = sheet.row_count

            self.app.sheet = sheet
            self.status_icon.config(text="🟢")

        except:
            self.app.sheet = None
            self.status_icon.config(text="🔴")

    # ---------- CLOCK IN (USES EMPTY ROW) ----------

    def clock_in(self):
        if not self.app.sheet:
            messagebox.showerror("Error", "Client not ready.")
            return

        now = datetime.datetime.now()
        config = load_config()

        row_index = self.app.get_first_empty_row()

        self.app.sheet.update(
            f"A{row_index}:F{row_index}",
            [[
                config["name"],
                "Clocked In",
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                "",
                "Active"
            ]]
        )

        self.app.current_row = row_index
        self.app.is_clocked_in = True
        self.app.active_start = now
        self.app.total_active = 0

        threading.Thread(target=self.app.monitor_idle, daemon=True).start()

        self.client_dropdown.config(state="disabled")

        self.clock_in_btn.pack_forget()
        self.clock_out_btn.pack(pady=10)

        self.status_label.config(text="Clocked In")
        self.timestamp_label.config(
            text=f"Clocked in at {now.strftime('%I:%M %p')}"
        )

        self.update_timer()

    # ---------- CLOCK OUT (WRITES TO NEXT ROW) ----------

    def clock_out(self):
        now = datetime.datetime.now()
        self.app.total_active += (now - self.app.active_start).seconds

        h = self.app.total_active // 3600
        m = (self.app.total_active % 3600) // 60
        s = self.app.total_active % 60

        next_row = self.app.current_row + 1

        self.app.sheet.update(
            f"A{next_row}:F{next_row}",
            [[
                load_config()["name"],
                "Clocked Out",
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                f"{h:02}:{m:02}:{s:02}",
                "Inactive"
            ]]
        )

        self.client_dropdown.config(state="readonly")

        self.clock_out_btn.pack_forget()
        self.clock_in_btn.pack(pady=10)

        self.status_label.config(text="Clocked Out")
        self.timestamp_label.config(
            text=f"Clocked out at {now.strftime('%I:%M %p')}"
        )

        self.total_label.config(text=f"{h:02}:{m:02}:{s:02}")

        self.app.is_clocked_in = False

    def update_timer(self):
        if not self.app.is_clocked_in:
            return

        now = datetime.datetime.now()
        elapsed = self.app.total_active

        if self.app.current_activity == "Active":
            elapsed += (now - self.app.active_start).seconds

        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60

        self.total_label.config(text=f"{h:02}:{m:02}:{s:02}")
        self.after(1000, self.update_timer)


# ================= RUN =================

app = TimeTrackerApp()
app.mainloop()