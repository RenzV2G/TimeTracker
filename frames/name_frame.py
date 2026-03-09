import tkinter as tk
from tkinter import ttk, messagebox
from config import save_config

class NameFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ttk.Label(self, text="Enter Your Name", font=("Segoe UI", 20)).pack(pady=80)
        
        self.entry = ttk.Entry(self, width=30)
        self.entry.pack()
        
        ttk.Button(self, text="Save", command=self.save, style="Save.TButton").pack(pady=20)
    
    def refresh(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.app.config_data.get("name", ""))
    
    def save(self):
        name = self.entry.get().strip()

        if not name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return

        self.app.config_data["name"] = name

        save_config(self.app.auth.user_email, self.app.config_data)

        self.app.auto_navigate()