# frames/dashboard_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import time
from config import load_config
from utils import get_current_timestamp, format_time
from constants import ICON_GREEN, ICON_YELLOW, ICON_RED, ICON_GRAY, IDLE_THRESHOLD

# Remove direct imports of other frames
# We'll use string references or import inside methods

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.state = None  # Will be initialized in refresh
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI."""
        self.setup_header()
        self.setup_client_section()
        self.setup_status_section()
        self.setup_buttons()
    
    def setup_header(self):
        """Setup the header section."""
        header = ttk.Frame(self)
        header.pack(fill="x")
        
        ttk.Label(header, text="Dashboard", style="Header.TLabel").pack(side="left")
        
        # Settings menu
        settings_btn = ttk.Menubutton(header, text="⚙")
        menu = tk.Menu(settings_btn, tearoff=0)
        
        # Use lambda with app.show_frame and class name as string
        menu.add_command(label="Edit Name", 
                        command=lambda: self.app.show_frame_by_name("NameFrame"))
        menu.add_command(label="Sign Out", command=self.app.sign_out)
        settings_btn["menu"] = menu
        settings_btn.pack(side="right")
        
        ttk.Separator(self).pack(fill="x", pady=10)
        
        self.greeting = ttk.Label(self, font=("Segoe UI", 13))
        self.greeting.pack(pady=5)
    
    def setup_client_section(self):
        """Setup the client selection section."""
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
        
        self.status_icon = tk.Label(row, text=ICON_GRAY, font=("Segoe UI", 14),
                                   bg="#f4f6f9")
        self.status_icon.pack(side="left", padx=5)
    
    def setup_status_section(self):
        """Setup the status display section."""
        self.status_label = ttk.Label(self, text="Not Clocked In")
        self.status_label.pack()
        
        self.timestamp_label = ttk.Label(self, text="Last Action: --")
        self.timestamp_label.pack()
        
        self.total_label = ttk.Label(self, text="00:00:00",
                                    font=("Segoe UI", 22, "bold"))
        self.total_label.pack(pady=15)
    
    def setup_buttons(self):
        """Setup action buttons."""
        # Use string reference instead of direct import
        ttk.Button(self,
                   text="Sheets",
                   command=lambda: self.app.show_frame_by_name("SheetFrame"),
                   style="Primary.TButton").pack(pady=5)
        
        ttk.Separator(self).pack(fill="x", pady=10)
        
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
        """Refresh the dashboard data."""
        # Import here to avoid circular imports
        from models import TimeTrackerState
        
        config = load_config()
        self.greeting.config(text=f"Hello, {config.get('name','')} 👋")
        
        clients = list(config.get("clients", {}).keys())
        self.client_dropdown["values"] = clients
        
        # Reset state
        self.state = TimeTrackerState()
        self.update_button_state()
    
    def load_client(self, event=None):
        """Load the selected client's sheet."""
        self.status_icon.config(text=ICON_YELLOW)
        
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
            self.status_icon.config(text=ICON_GREEN)
            
        except Exception as e:
            print(f"Error loading client: {e}")
            self.app.sheet = None
            if self.state:
                self.state.sheet = None
            self.status_icon.config(text=ICON_RED)
    
    def get_first_empty_row(self):
        """Get the first empty row in the sheet."""
        data = self.app.sheet.get_all_values()
        
        for i, row in enumerate(data, start=1):
            if not any(cell.strip() for cell in row):
                return i
        
        return len(data) + 1
    
    def clock_in(self):
        """Clock in to the current client."""
        if not self.app.sheet:
            messagebox.showerror("Error", "Client not ready.")
            return
        
        timestamp = get_current_timestamp()
        config = load_config()
        row_index = self.get_first_empty_row()
        
        # Write to sheet
        self.app.sheet.update(
            f"A{row_index}:F{row_index}",
            [[
                config["name"],
                "Clocked In",
                timestamp['date'],
                timestamp['time'],
                "",
                "Active"
            ]]
        )
        
        # Update state
        if self.state:
            self.state.clock_in(row_index, timestamp['datetime'])
        
        self.app.is_clocked_in = True
        self.app.current_row = row_index
        self.app.active_start = timestamp['datetime']
        self.app.total_active = 0
        self.app.last_activity = timestamp['datetime']
        self.app.current_activity = "Active"
        
        # Start monitoring
        threading.Thread(target=self.monitor_idle, daemon=True).start()
        
        # Update UI
        self.client_dropdown.config(state="disabled")
        self.update_button_state()
        self.status_label.config(text="Clocked In")
        self.timestamp_label.config(text=f"Clocked in at {timestamp['formatted_time']}")
        
        self.update_timer()
    
    def clock_out(self):
        """Clock out from the current client."""
        timestamp = get_current_timestamp()
        
        if self.state:
            self.state.clock_out(timestamp['datetime'])
            total_formatted = format_time(self.state.get_total_seconds(timestamp['datetime']))
        else:
            # Fallback if state is not available
            self.app.total_active += (timestamp['datetime'] - self.app.active_start).seconds
            total_formatted = format_time(self.app.total_active)
        
        next_row = self.app.current_row + 1
        
        # Write to sheet
        self.app.sheet.update(
            f"A{next_row}:F{next_row}",
            [[
                load_config()["name"],
                "Clocked Out",
                timestamp['date'],
                timestamp['time'],
                total_formatted,
                "Inactive"
            ]]
        )
        
        # Update UI
        self.client_dropdown.config(state="readonly")
        self.update_button_state()
        self.status_label.config(text="Clocked Out")
        self.timestamp_label.config(text=f"Clocked out at {timestamp['formatted_time']}")
        self.total_label.config(text=total_formatted)
        
        self.app.is_clocked_in = False
    
    def update_button_state(self):
        """Update button visibility based on clock state."""
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
        """Update the timer display."""
        if not (self.state and self.state.is_clocked_in) and not self.app.is_clocked_in:
            return
        
        now = datetime.datetime.now()
        
        if self.state:
            total_formatted = format_time(self.state.get_total_seconds(now))
        else:
            # Fallback calculation
            elapsed = self.app.total_active
            if self.app.current_activity == "Active":
                elapsed += (now - self.app.active_start).seconds
            total_formatted = format_time(elapsed)
        
        self.total_label.config(text=total_formatted)
        self.after(1000, self.update_timer)
    
    def monitor_idle(self):
        """Monitor user idle time."""
        while self.app.is_clocked_in:
            idle_time = (datetime.datetime.now() - self.app.last_activity).seconds
            
            if idle_time >= IDLE_THRESHOLD and self.app.current_activity == "Active":
                if self.state:
                    self.state.total_active += (datetime.datetime.now() - self.state.active_start).seconds
                self.app.total_active += (datetime.datetime.now() - self.app.active_start).seconds
                self.app.sheet.update(f"F{self.app.current_row}", "Idle")
                self.app.current_activity = "Idle"
            elif idle_time < IDLE_THRESHOLD and self.app.current_activity == "Idle":
                self.app.active_start = datetime.datetime.now()
                if self.state:
                    self.state.active_start = self.app.active_start
                self.app.sheet.update(f"F{self.app.current_row}", "Active")
                self.app.current_activity = "Active"
            
            time.sleep(5)