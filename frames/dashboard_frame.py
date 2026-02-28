import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import time
from config import load_config
from utils import get_current_timestamp, format_time
from constants import IDLE_THRESHOLD


class DashboardFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.state = None
        self.setup_ui()

    def setup_ui(self):
        self.setup_header()
        self.setup_client_section()
        self.setup_status_section()
        self.setup_buttons()

    def setup_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Label(header, text="Dashboard", style="Header.TLabel").pack(side="left")

        settings_btn = ttk.Menubutton(header, text="⚙")
        menu = tk.Menu(settings_btn, tearoff=0)

        menu.add_command(
            label="Edit Name", command=lambda: self.app.show_frame_by_name("NameFrame")
        )
        menu.add_command(label="Sign Out", command=self.app.sign_out)
        settings_btn["menu"] = menu
        settings_btn.pack(side="right")

        ttk.Separator(self).pack(fill="x", pady=10)

        self.greeting = ttk.Label(self, font=("Segoe UI", 13))
        self.greeting.pack(pady=5)

    def setup_client_section(self):
        row = ttk.Frame(self)
        row.pack()

        self.client_var = tk.StringVar()
        self.client_dropdown = ttk.Combobox(
            row, textvariable=self.client_var, state="readonly", width=28
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
    def set_status_color(self, color):
        self.status_canvas.itemconfig(self.status_circle, fill=color)

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

        self.daily_total_label = ttk.Label(
            self, text="Today's Total: --", 
            font=("Segoe UI", 11)
        )
        self.daily_total_label.pack(pady=5)

    def setup_buttons(self):
        ttk.Button(
            self,
            text="Sheets",
            command=lambda: self.app.show_frame_by_name("SheetFrame"),
            style="Primary.TButton",
        ).pack(pady=5)

        ttk.Separator(self).pack(fill="x", pady=10)

        self.clock_in_btn = ttk.Button(
            self, text="Clock In", command=self.clock_in, style="Primary.TButton"
        )
        self.clock_out_btn = ttk.Button(
            self, text="Clock Out", command=self.clock_out, style="Primary.TButton"
        )

        self.clock_in_btn.pack(pady=10)


#  ----- Functionalities -----
    def refresh(self):
        from models import TimeTrackerState

        config = load_config()
        self.greeting.config(text=f"Hello, {config.get('name','')} 👋")

        clients = list(config.get("clients", {}).keys())
        self.client_dropdown["values"] = clients

        self.state = TimeTrackerState()
        self.update_button_state()

    def load_client(self, event=None):
        self.set_status_color("orange")

        config = load_config()
        client_name = self.client_var.get()
        client_data = config["clients"].get(client_name)

        try:
            client = self.app.authenticate()
            sheet = client.open_by_key(client_data["sheet_id"]).sheet1
            _ = sheet.row_count

            self.app.sheet = sheet
            if self.state:
                self.state.sheet = sheet
            self.set_status_color("green")

        except Exception as e:
            print(f"Error loading client: {e}")
            self.app.sheet = None
            if self.state:
                self.state.sheet = None
            self.set_status_color("red")

    def get_first_empty_row(self):
        data = self.app.sheet.get_all_values()

        for i, row in enumerate(data, start=1):
            if not any(cell.strip() for cell in row):
                return i

        return len(data) + 1

    def ensure_row_capacity(self, row_index):
        current_max = self.app.sheet.row_count

        if row_index > current_max:
            rows_to_add = row_index - current_max
            self.app.sheet.add_rows(rows_to_add)

    def clock_in(self):
        if not self.app.sheet:
            messagebox.showerror("Error", "Client not ready.")
            return

        timestamp = get_current_timestamp()
        config = load_config()
        row_index = self.get_first_empty_row()
        self.ensure_row_capacity(row_index)

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

        if self.state:
            self.state.clock_in(row_index, timestamp["datetime"])

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
        self.app.is_clocked_in = False

        timestamp = get_current_timestamp()

        if self.state:
            self.state.clock_out(timestamp["datetime"])
            total_formatted = format_time(
                self.state.get_total_seconds(timestamp["datetime"])
            )
        else:
            self.app.total_active += (
                timestamp["datetime"] - self.app.active_start
            ).seconds
            total_formatted = format_time(self.app.total_active)

        next_row = self.app.current_row + 1
        self.ensure_row_capacity(next_row)

        self.app.sheet.update(
            f"A{next_row}:F{next_row}",
            [
                [
                    load_config()["name"],
                    "Clocked Out",
                    timestamp["date"],
                    timestamp["time"],
                    total_formatted,
                    "Inactive",
                ]
            ],
        )

        self.client_dropdown.config(state="readonly")
        self.update_button_state()
        self.status_label.config(text="Clocked Out")
        self.timestamp_label.config(
            text=f"Clocked out at {timestamp['formatted_time']}"
        )
        self.total_label.config(text=total_formatted)

    def update_button_state(self):
        if self.state and self.state.is_clocked_in:
            self.clock_in_btn.pack_forget()
            self.clock_out_btn.pack(pady=10)
        elif self.app.is_clocked_in:
            self.clock_in_btn.pack_forget()
            self.clock_out_btn.pack(pady=10)
        else:
            self.clock_out_btn.pack_forget()
            self.clock_in_btn.pack(pady=10)

    def update_timer(self):
        if not (self.state and self.state.is_clocked_in) and not self.app.is_clocked_in:
            return

        now = datetime.datetime.now()

        if self.state:
            total_formatted = format_time(self.state.get_total_seconds(now))
        else:
            elapsed = self.app.total_active
            if self.app.current_activity == "Active":
                elapsed += (now - self.app.active_start).seconds
                total_formatted = format_time(elapsed)

        self.total_label.config(text=total_formatted)
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        if self.state:
            total_seconds = self.state.get_total_seconds(now)
        else:
            total_seconds = elapsed

        self.daily_total_label.config(
            text=f"Your total rendered {today} - {format_time(total_seconds)}"
        )

        self.after(1000, self.update_timer)

    def monitor_idle(self):
        while self.app.is_clocked_in:
            now = datetime.datetime.now()
            idle_time = (now - self.app.last_activity).seconds

            # ---- ACTIVE ➜ IDLE ----
            if idle_time >= IDLE_THRESHOLD and self.app.current_activity == "Active":
                
                # ✅ SAVE elapsed active time before going idle
                self.app.total_active += (now - self.app.active_start).seconds
                
                self.app.current_activity = "Idle"
                self.app.sheet.update(f"F{self.app.current_row}", [["Idle"]])

            # ---- IDLE ➜ ACTIVE ----
            elif idle_time < IDLE_THRESHOLD and self.app.current_activity == "Idle":
                
                self.app.active_start = now
                self.app.current_activity = "Active"
                self.app.sheet.update(f"F{self.app.current_row}", [["Active"]])

            time.sleep(1)