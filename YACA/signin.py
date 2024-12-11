import tkinter as tk
from tkinter import messagebox
from google_sso import google_login, get_user_info
from clockface import ClockFace  # Import ClockFace
from datetime import datetime  # Import datetime

class SignInPage:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("Sign In")
        
        self.center_window(400, 300)  # Center the window with desired dimensions
        
        self.clock_face = ClockFace(root)  # Initialize the ClockFace
        self.clock_face.pack(pady=(10, 0))  # Use pack layout and reduce padding
        
        self.date_label = tk.Label(root, font=("Helvetica", 16))
        self.date_label.pack(pady=(0, 10))  # Ensure date_label is always visible
        self.update_date()
        
        self.signin_button = tk.Button(root, text="Sign In with Google", command=self.sign_in)
        self.signin_button.pack(pady=20)
    
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def update_date(self):
        today = datetime.now().strftime("%a, %B %d")
        self.date_label.config(text=today)
        self.root.after(86400000, self.update_date)  # Update date every 24 hours
    
    def sign_in(self):
        try:
            creds = google_login()
            user_info = get_user_info(creds)
            self.on_success(user_info)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hide(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()

if __name__ == "__main__":
    def main():
        def on_success(user_info):
            print(f"Logged in as {user_info['name']}")
            signin_page.hide()  # Hide the sign-in window
            # Proceed to the next page (e.g., ClockPage)
            # clock_page = ClockPage()  # Assuming you have a ClockPage class
            # clock_page.show()

        root = tk.Tk()
        signin_page = SignInPage(root, on_success)
        root.mainloop()

    main()