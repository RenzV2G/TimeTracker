import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import os
import winsound
import time
from utils import get_current_timestamp, format_time, resource_path
from constants import IDLE_THRESHOLD


class DashboardFrame(ttk.Frame):
    """
    Main dashboard UI.
    Handles:
    - Client selection
    - Clock in / out
    - Idle monitoring
    - UI state management
    """
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.state = None
        self.setup_ui()

        self.app.protocol("WM_DELETE_WINDOW", self.on_close)
    

    # --------- UI SETUP ----------
    def setup_ui(self):
        self.setup_header()
        self.setup_client_section()
        self.setup_status_section()
        self.setup_buttons()

    def setup_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Label(header, text="Dashboard", style="Header.TLabel").pack(side="left")

        settings_btn = ttk.Menubutton(header, text="Settings")
        menu = tk.Menu(settings_btn, tearoff=0)
        menu.add_command(label="Edit Name", command=lambda: self.app.show_frame_by_name("NameFrame"))
        menu.add_command(label="Sign Out", command=self.app.sign_out)
        
        settings_btn["menu"] = menu
        settings_btn.pack(side="right")

        ttk.Separator(self).pack(fill="x", pady=10)

        self.greeting = ttk.Label(self, font=("Segoe UI", 13, "bold"))
        self.greeting.pack(pady=5)

    def setup_client_section(self):
        row = ttk.Frame(self)
        row.pack(pady=5)

        self.client_var = tk.StringVar(value="Please select a client")
        self.client_dropdown = ttk.Combobox(
            row, 
            textvariable=self.client_var, 
            state="readonly", 
            width=28
        )
        self.client_dropdown.pack(side="left")
        self.client_dropdown.bind("<<ComboboxSelected>>", self.load_client)

        self.status_canvas = tk.Canvas(
            row,
            width=16,
            height=16,
            highlightthickness=0,
            bg="#f4f6f9"
        )
        self.status_canvas.pack(side="left", padx=5)

        self.status_circle = self.status_canvas.create_oval(
            2, 2, 14, 14,
            fill="gray"
        )

        ttk.Button(
            self,
            text="Sheets",
            command=lambda: self.app.show_frame_by_name("SheetFrame"),
            style="Primary.TButton",
        ).pack(pady=5)

    def setup_status_section(self):
        self.status_label = ttk.Label(self, text="Not Clocked In")
        self.status_label.pack()

        self.timestamp_label = ttk.Label(self, text="Last Action: --")
        self.timestamp_label.pack()

        self.total_label = ttk.Label(
            self, text="00:00:00", 
            font=("Segoe UI", 22, "bold")
        )
        self.total_label.pack(pady=15)

        self.daily_total_label = ttk.Label(self)
        self.daily_total_label.pack()

    def setup_buttons(self):
        ttk.Separator(self).pack(fill="x", pady=10)

        self.clock_in_btn = ttk.Button(
            self, text="Clock In", command=self.clock_in, style="Primary.TButton"
        )
        self.clock_out_btn = ttk.Button(
            self, text="Clock Out", command=self.clock_out, style="Primary.TButton"
        )

        self.clock_in_btn.pack(pady=10)


#  ----- Functionalities -----
    # Clock in and sheets ready SFX
    def play_sound(self, filename):
        try:
            sound_path = resource_path(f"sounds/{filename}")
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print("Sound error:", e)

    def set_status_color(self, color):
        self.status_canvas.itemconfig(self.status_circle, fill=color)

        if color == "green":
            self.play_sound("ready_ping.wav")

    # The dropdown menu checks validates or run a test check if the clientURL is working
    def refresh(self):
        from models import TimeTrackerState
        self.set_status_color("gray")

        config = self.app.config_data
        self.greeting.config(text=f"Hello, {config.get('name','')}")

        clients = list(config.get("clients", {}).keys())
        self.client_dropdown["values"] = clients

        self.client_var.set("Please select a client")
        self.app.sheet = None
        self.app.current_client = None

        self.state = TimeTrackerState()
        self.update_button_state()

    def load_client(self, event=None):
        client_name = self.client_var.get()

        if client_name == "Please select a client":
            return
        self.set_status_color("orange")
        
        config = self.app.config_data
        client_data = config["clients"].get(client_name)

        try:
            client = self.app.client
            self.app.sheet = client.open_by_key(client_data["sheet_id"]).sheet1
            self.set_status_color("green")

        except Exception as e:
            self.app.sheet = None
            self.set_status_color("red")
            messagebox.showerror(
                "Sheet Access Error",
                "Cannot access this Google Sheet.\n\n"
                "Make sure:\n"
                "• The sheet exists\n"
                "• The account has permission\n"
                "• The Sheet ID is correct"
            )

    # To get the first empty row for the system to input the clockin or clockout to the sheets
    def get_first_empty_row(self):
        values = self.app.sheet.get_all_values()
        row_count = self.app.sheet.row_count

        # Scan existing rows
        for index, row in enumerate(values, start=1):
            if not any(cell.strip() for cell in row):
                return index

        # No empty row found
        next_row = len(values) + 1

        if next_row > row_count:
            self.app.sheet.add_rows(next_row - row_count)

        return next_row

    def clock_in(self):
        if not self.app.sheet:
            messagebox.showerror("Error", "Client not ready.")
            return

        timestamp = get_current_timestamp()
        config = self.app.config_data
        row_index = self.get_first_empty_row()

        self.app.sheet.update(
            f"A{row_index}:F{row_index}",
            [
                [
                    config["name"],
                    "Clocked In",
                    timestamp["date"],
                    timestamp["time"],
                    "",
                    "Active",
                ]
            ],
        )

        self.app.is_clocked_in = True
        self.app.current_row = row_index
        self.app.active_start = timestamp["datetime"]
        self.app.total_active = 0
        self.app.last_activity = timestamp["datetime"]
        self.app.current_activity = "Active"

        threading.Thread(target=self.monitor_idle, daemon=True).start()

        self.client_dropdown.config(state="disabled")
        self.update_button_state()
        self.status_label.config(text="Clocked In")
        self.timestamp_label.config(text=f"Clocked in at {timestamp['formatted_time']}")

        self.update_timer()

    def clock_out(self):
        timestamp = get_current_timestamp()

        if self.app.current_activity == "Active":
            self.app.total_active += (
                timestamp["datetime"] - self.app.active_start
            ).seconds

        total_formatted = format_time(self.app.total_active)

        next_row = self.get_first_empty_row()

        self.app.sheet.update(
            f"A{next_row}:F{next_row}",
            [[
                self.app.config_data["name"],
                "Clocked Out",
                timestamp["date"],
                timestamp["time"],
                total_formatted,
                "Inactive",
            ]]
        )

        self.app.is_clocked_in = False
        self.client_dropdown.config(state="readonly")

        self.update_button_state()
        self.status_label.config(text="Clocked Out")
        self.timestamp_label.config(
            text=f"Clocked out at {timestamp['formatted_time']}"
        )
        self.total_label.config(text=total_formatted)

        self.play_sound("clock_out.wav")

    # To hide the clockin button if the user is already in clockedin, and show the clock out button. and vice versa
    def update_button_state(self):
        if self.app.is_clocked_in:
            self.clock_in_btn.pack_forget()
            self.clock_out_btn.pack(pady=10)
        else:
            self.clock_out_btn.pack_forget()
            self.clock_in_btn.pack(pady=10)

    # Status update of the clock
    def update_timer(self):
        if not self.app.is_clocked_in:
            return

        now = datetime.datetime.now()
        elapsed = self.app.total_active

        if self.app.current_activity == "Active":
            elapsed += (now - self.app.active_start).seconds

        formatted = format_time(elapsed)

        self.total_label.config(text=formatted)
        today = now.strftime("%Y-%m-%d")
        self.daily_total_label.config(
            text=f"Your total rendered {today} - {formatted}"
        )

        self.after(1000, self.update_timer)

    # The mouse idle monitoring detection
    def monitor_idle(self):
        while self.app.is_clocked_in:
            now = datetime.datetime.now()
            idle_time = (now - self.app.last_activity).seconds

            if idle_time >= IDLE_THRESHOLD and self.app.current_activity == "Active":
                self.app.total_active += (now - self.app.active_start).seconds
                self.app.current_activity = "Idle"
                self.app.sheet.update(f"F{self.app.current_row}", [["Idle"]])

            elif idle_time < IDLE_THRESHOLD and self.app.current_activity == "Idle":
                self.app.active_start = now
                self.app.current_activity = "Active"
                self.app.sheet.update(f"F{self.app.current_row}", [["Active"]])

            time.sleep(2)

    # App accidental close detection
    def on_close(self):
        if self.app.is_clocked_in:
            messagebox.showwarning(
                "Warning",
                "You are currently clocked in.\nPlease clock out before exiting."
            )
        else:
            self.app.destroy()