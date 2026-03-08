import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from pynput import mouse
import os

from auth import GoogleAuth
from config import load_config, save_config, get_config_file
from constants import BG_COLOR
from frames import SignInFrame, NameFrame, SheetFrame, DashboardFrame

class TimeTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Freelance Time Tracker")
        self.geometry("520x525")
        self.resizable(False, False)
        
        self.setup_styles()
        self.configure(bg=BG_COLOR)
        
        self.auth = GoogleAuth()
        self.config_data = {}
        
        # State variables
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
        self.frames_by_name = {}  
        
        for F in (SignInFrame, NameFrame, SheetFrame, DashboardFrame):
            frame = F(container, self)
            self.frames[F] = frame
            self.frames_by_name[F.__name__] = frame  
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.auto_navigate()
        
        mouse.Listener(on_move=self.on_move).start()
    
    def show_frame_by_name(self, frame_name):
        if frame_name in self.frames_by_name:
            frame = self.frames_by_name[frame_name]
            frame.tkraise()
            if hasattr(frame, "refresh"):
                frame.refresh()
    
    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, 
                            font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", 
                            font=("Segoe UI", 18, "bold"))
        
        self.style.configure("Primary.TButton",
                            font=("Segoe UI", 10, "bold"),
                            padding=6)
        
        self.style.configure("Delete.TButton",
                             font=("Segoe UI", 10, "bold"),
                             background="#D32F2F",
                             foreground="white",
                             padding=6 )
        self.style.map("Delete.TButton", background=[("active", "#B71C1C")])
        
        self.style.configure("Edit.TButton",
                             font=("Segoe UI", 10, "bold"),
                             background="#1976D2",
                             foreground="white",
                             padding=6 )
        self.style.map("Edit.TButton", background=[("active", "#1565C0")])
      
        self.style.configure("Save.TButton",
                             font=("Segoe UI", 10, "bold"),
                             background="#06B43A",
                             foreground="white",
                             padding=6 )
        self.style.map("Save.TButton", background=[("active", "#378541")])
        
        self.style.configure("Treeview",
                            font=("Segoe UI", 10),
                            rowheight=28)
        self.style.configure("Treeview.Heading",
                            font=("Segoe UI", 10, "bold"))
    
    def authenticate(self):
        return self.auth.authenticate()
    
    def sign_out(self):
        if self.is_clocked_in:
            messagebox.showwarning(
                "Clock In Active",
                "You must clock out before signing out."
            )
            return

        answer = messagebox.askyesnocancel(
            "Sign Out",
            "Do you want to save your configuration before signing out?"
        )

        if answer is None:
            return
    
        if answer:
            save_config(self.auth.user_email, self.config_data)
        else:
            config_path = get_config_file(self.auth.user_email)
            if os.path.exists(config_path):
                os.remove(config_path)

        self.sheet = None
        self.current_client = None
        self.is_clocked_in = False
        self.current_activity = None

        self.auth.sign_out()

        self.client = None
        self.config_data = {}

        self.show_frame(SignInFrame)
    
    def auto_navigate(self):
        if not self.auth.is_logged_in():
            self.show_frame(SignInFrame)
            return
        
        try:
            self.client = self.auth.authenticate()
            email = self.auth.user_email
            self.config_data = load_config(email)

        except Exception:
            messagebox.showwarning(
                "Session Expired",
                "Your login session expired. Please sign in again"
            )
            self.auth.sign_out()
            self.show_frame(SignInFrame)
            return
        
        if not self.config_data.get("name"):
            self.show_frame(NameFrame)
        else:
            self.show_frame(DashboardFrame)
    
    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, "refresh"):
            frame.refresh()
    
    def on_move(self, x, y):
        self.last_activity = datetime.datetime.now()


if __name__ == "__main__":
    app = TimeTrackerApp()
    app.mainloop()