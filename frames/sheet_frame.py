import tkinter as tk
from tkinter import ttk, messagebox
from config import save_config
from utils import extract_sheet_id

class SheetFrame(ttk.Frame):
    # UI setup of the sheet frame
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self,
                  text="Manage Client Sheets",
                  style="Header.TLabel").pack(pady=15)

        self.setup_table()
        self.setup_buttons()

    def setup_table(self):
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10)

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Client", "SheetID"),
            show="headings",
            height=8,
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=self.tree.yview)

        self.tree.heading("Client", text="Client")
        self.tree.heading("SheetID", text="Sheet ID")

        self.tree.column("Client", width=180, anchor="center")
        self.tree.column("SheetID", width=260, anchor="center")

        self.tree.pack()

    def setup_buttons(self):
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10)

        self.edit_btn = ttk.Button(
            action_frame,
            text="Edit",
            command=self.edit_selected,
            style="Edit.TButton"
        )
        self.edit_btn.pack(side="left", padx=10)

        self.delete_btn = ttk.Button(
            action_frame,
            text="Delete",
            command=self.delete_selected,
            style="Delete.TButton"
        )
        self.delete_btn.pack(side="left", padx=10)

        ttk.Button(self,
                   text="Add New Client",
                   command=self.add_popup,
                   style="Primary.TButton").pack(pady=5)

        ttk.Button(self,
                   text="Back to Dashboard",
                   command=lambda: self.app.show_frame_by_name("DashboardFrame"),
                   style="Primary.TButton").pack(pady=5)

    # Core functionalities of the sheets frame
    def refresh(self):
        self.tree.delete(*self.tree.get_children())

        config = self.app.config_data
        for name, data in config.get("clients", {}).items():
            self.tree.insert("", "end", values=(name, data["sheet_id"]))
    # Detect if user is currently selected an client to edit nor delete
    def get_selected_client(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Client", "Please select a client.")
            return None
        return self.tree.item(selected[0])["values"][0]
    # To Edit the selected client function
    def edit_selected(self):
        client = self.get_selected_client()
        if client:
            self.edit_popup(client)
    # To Delete the selected client function
    def delete_selected(self):
        client = self.get_selected_client()
        if not client:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete '{client}'?",
            icon='warning'
        )
        if confirm:
            config = self.app.config_data
            del config["clients"][client]
            save_config(self.app.auth.user_email, config)
            self.refresh()
            messagebox.showinfo("Success", f"Client '{client}' has been deleted.")

    # The popup function to show the edit pop up
    def add_popup(self):
        self.edit_popup()

    # The edit pop up window where it pops when the user adds or edit the sheets/client url
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
        
        help_text = "Example: https://docs.google.com/spreadsheets/d/1abc123def456/edit"
        ttk.Label(popup, text=help_text, font=("Segoe UI", 8), foreground="gray").pack(pady=(0, 15))

        if client_name:
            config = self.app.config_data
            data = config["clients"][client_name]
            name_entry.insert(0, client_name)
            url_entry.insert(0, data["sheet_url"])

        def save():
            try:
                name = name_entry.get().strip()
                url = url_entry.get().strip()

                if not name:
                    raise Exception("Client name cannot be empty.")

                sheet_id = extract_sheet_id(url)
                if not sheet_id:
                    raise Exception("Invalid Google Sheets URL.")

                client = self.app.authenticate()
                sheet = client.open_by_key(sheet_id).sheet1
                _ = sheet.row_count  

                config = self.app.config_data
                clients = config.get("clients", {})


                for existing_name in clients.keys():
                    if (
                        existing_name.lower() == name.lower()
                        and existing_name != client_name  
                    ):
                        raise Exception("Client name already exists.")

                for existing_name, data in clients.items():
                    if data["sheet_id"] == sheet_id and existing_name != client_name:
                        raise Exception(
                            "This Google Sheet is already assigned to another client."
                        )

                config["clients"][name] = {"sheet_url": url, "sheet_id": sheet_id}

                if client_name and client_name != name:
                    del config["clients"][client_name]

                save_config(self.app.auth.user_email, config)

                popup.destroy()
                self.refresh()

                messagebox.showinfo("Success", "Client saved successfully.")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(popup, text="Save", command=save, style="Save.TButton").pack(
            pady=15
        )



