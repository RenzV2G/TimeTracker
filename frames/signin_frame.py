from tkinter import ttk, messagebox

class SignInFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ttk.Label(self, text="Sign in to Google", font=("Segoe UI", 18)).pack(pady=80)
        ttk.Button(self, text="Sign In", command=self.login).pack()
    
    def login(self):
        try:
            self.app.client = self.app.authenticate()
            self.app.auto_navigate()
        except Exception as e:
            messagebox.showerror("Authentication", str(e))