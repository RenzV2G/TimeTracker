# frames/sheet_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from config import load_config, save_config
from utils import extract_sheet_id

# Remove direct import of DashboardFrame

class SheetFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        ttk.Label(self,
                  text="Manage Client Sheets",
                  style="Header.TLabel").pack(pady=15)
        
        self.setup_table()
        self.setup_buttons()
    
    def setup_table(self):
        """Setup the treeview table."""
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
    
    def setup_buttons(self):
        """Setup action buttons."""
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
        
        # Use string reference instead of direct import
        ttk.Button(self,
                   text="Back to Dashboard",
                   command=lambda: self.app.show_frame_by_name("DashboardFrame"),
                   style="Primary.TButton").pack(pady=5)
    
    def refresh(self):
        """Refresh the table data."""
        self.tree.delete(*self.tree.get_children())
        
        config = load_config()
        for name, data in config.get("clients", {}).items():
            self.tree.insert("", "end", values=(name, data["sheet_id"]))
    
    def get_selected_client(self):
        """Get the selected client name."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Client", "Please select a client.")
            return None
        return self.tree.item(selected[0])["values"][0]
    
    def edit_selected(self):
        """Edit the selected client."""
        client = self.get_selected_client()
        if client:
            self.edit_popup(client)
    
    def delete_selected(self):
        """Delete the selected client."""
        client = self.get_selected_client()
        if not client:
            return
        
        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{client}'?")
        if confirm:
            config = load_config()
            del config["clients"][client]
            save_config(config)
            self.refresh()
    
    def add_popup(self):
        """Show popup to add new client."""
        self.edit_popup()
    
    def edit_popup(self, client_name=None):
        """Show popup to edit client."""
        popup = tk.Toplevel(self)
        popup.title("Client Setup")
        popup.geometry("400x250")
        popup.configure(bg="#f4f6f9")
        
        # Name field
        ttk.Label(popup, text="Client Name").pack(pady=5)
        name_entry = ttk.Entry(popup, width=40)
        name_entry.pack()
        
        # URL field
        ttk.Label(popup, text="Google Sheet URL").pack(pady=5)
        url_entry = ttk.Entry(popup, width=40)
        url_entry.pack()
        
        # Populate if editing
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
                
                # Test connection
                client = self.app.authenticate()
                sheet = client.open_by_key(sheet_id).sheet1
                _ = sheet.row_count
                
                # Save to config
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
        
        ttk.Button(popup, text="Save", command=save, style="Primary.TButton").pack(pady=15)