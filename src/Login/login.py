import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import re
from PIL import Image, ImageTk
import time

class LoginPortal:
    def __init__(self, master, on_success):
        # Store the master window and callback
        self.master = master
        self.on_success = on_success
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(master, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Add company logo/brand (placeholder)
        self.logo_label = ttk.Label(
            self.main_frame,
            text="🔐",
            font=("SF Mono", 40)
        )
        self.logo_label.pack(pady=20)
        
        # Welcome message with better visibility and subtle animation
        self.welcome_frame = ttk.Frame(self.main_frame)
        self.welcome_frame.pack(fill=X, pady=10)
        
        self.welcome_label = ttk.Label(
            self.welcome_frame,
            text="Welcome Back",
            font=("SF Mono", 24, "bold"),
            bootstyle="primary"
        )
        self.welcome_label.pack(pady=10)
        
        # Add a subtitle for extra flair
        self.subtitle_label = ttk.Label(
            self.welcome_frame,
            text="We're glad to see you again!",
            font=("SF Mono", 12),
            bootstyle="secondary"
        )
        self.subtitle_label.pack()
        
        self.animate_welcome()
        
        # Login form frame
        self.form_frame = ttk.Frame(self.main_frame)
        self.form_frame.pack(fill=X, pady=20)
        
        # Username field with icon and validation
        self.username_frame = ttk.Frame(self.form_frame)
        self.username_frame.pack(fill=X, pady=10)
        
        ttk.Label(
            self.username_frame,
            text="👤",
            font=("SF Mono", 14)
        ).pack(side=LEFT, padx=5)
        
        self.username = ttk.Entry(
            self.username_frame,
            font=("SF Mono", 14),
            bootstyle="primary",
            width=30
        )
        self.username.pack(side=LEFT, padx=5)
        self.username.insert(0, "Username")
        self.username.bind("<FocusIn>", lambda e: self.on_entry_click(self.username, "Username"))
        self.username.bind("<FocusOut>", lambda e: self.on_focus_out(self.username, "Username"))
        
        # Password field with icon, show/hide functionality
        self.password_frame = ttk.Frame(self.form_frame)
        self.password_frame.pack(fill=X, pady=10)
        
        ttk.Label(
            self.password_frame,
            text="🔒",
            font=("SF Mono", 14)
        ).pack(side=LEFT, padx=5)
        
        self.password = ttk.Entry(
            self.password_frame,
            show="•",
            font=("SF Mono", 14),
            bootstyle="primary",
            width=30
        )
        self.password.pack(side=LEFT, padx=5)
        self.password.insert(0, "Password")
        self.password.bind("<FocusIn>", lambda e: self.on_entry_click(self.password, "Password"))
        self.password.bind("<FocusOut>", lambda e: self.on_focus_out(self.password, "Password"))
        
        # Show/Hide password button
        self.show_password = ttk.Button(
            self.password_frame,
            text="👁",
            command=self.toggle_password,
            bootstyle="primary-link",
            width=3
        )
        self.show_password.pack(side=LEFT)
        
        # Remember me checkbox
        self.remember = ttk.BooleanVar()
        self.remember_checkbox = ttk.Checkbutton(
            self.form_frame,
            text="Remember me",
            variable=self.remember,
            bootstyle="primary-round-toggle"
        )
        self.remember_checkbox.pack(pady=10)
        
        # Login button with loading animation
        self.login_button = ttk.Button(
            self.form_frame,
            text="Login",
            command=self.authenticate,
            bootstyle="primary",
            width=30
        )
        self.login_button.pack(pady=20)
        
        # Error message label
        self.error_label = ttk.Label(
            self.form_frame,
            text="",
            bootstyle="danger",
            font=("SF Mono", 12)
        )
        self.error_label.pack(pady=10)
        
        # Track login attempts
        self.login_attempts = 0
        self.locked_until = None
        
        # Bind enter key to login
        self.master.bind("<Return>", lambda e: self.authenticate())

    def animate_welcome(self):
        """Add subtle animation to welcome message"""
        def animate():
            for i in range(0, 10):
                self.welcome_label.configure(font=("SF Mono", 24 + i//5, "bold"))
                time.sleep(0.05)
                self.master.update()
            for i in range(10, 0, -1):
                self.welcome_label.configure(font=("SF Mono", 24 + i//5, "bold"))
                time.sleep(0.05)
                self.master.update()
        self.master.after(1000, animate)

    def on_entry_click(self, entry, default_text):
        """Clear placeholder text on click"""
        if entry.get() == default_text:
            entry.delete(0, tk.END)
            if entry == self.password:
                entry.configure(show="•")

    def on_focus_out(self, entry, default_text):
        """Restore placeholder text if empty"""
        if entry.get() == "":
            entry.insert(0, default_text)
            if entry == self.password and entry.get() == default_text:
                entry.configure(show="")

    def toggle_password(self):
        """Toggle password visibility"""
        current = self.password.cget("show")
        self.password.configure(show="" if current == "•" else "•")

    def show_error(self, message):
        """Display error message with animation"""
        self.error_label.configure(text=message)
        def fade_out():
            self.error_label.configure(text="")
        self.master.after(3000, fade_out)

    def authenticate(self):
        """Handle login authentication"""
        if self.locked_until and time.time() < self.locked_until:
            remaining = int(self.locked_until - time.time())
            self.show_error(f"Account locked. Try again in {remaining} seconds")
            return
        
        if not self.validate_input():
            return
        
        # Simulate loading
        self.login_button.configure(text="Logging in...", state="disabled")
        self.master.update()
        time.sleep(1)
        
        # Placeholder authentication
        if self.username.get() == "user" and self.password.get() == "password":
            self.login_button.configure(text="Success!", bootstyle="success")
            self.master.update()
            time.sleep(0.5)  # Short delay to show success message
            self.master.destroy()  # Close login window
            self.on_success()  # Call the success callback
        else:
            self.login_attempts += 1
            if self.login_attempts >= 3:
                self.locked_until = time.time() + 30
                self.show_error("Too many attempts. Account locked for 30 seconds")
            else:
                self.show_error(f"Invalid credentials ({3-self.login_attempts} attempts remaining)")
            self.login_button.configure(text="Login", state="normal")

    def validate_input(self):
        """Validate username and password"""
        username = self.username.get()
        password = self.password.get()
        
        if username == "Username" or password == "Password":
            self.show_error("Please enter both username and password")
            return False
        
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            self.show_error("Invalid username format")
            return False
        
        if len(password) < 6:
            self.show_error("Password must be at least 6 characters")
            return False
        
        return True

    def show_error(self, message):
        """Display error message with animation"""
        self.error_label.configure(text=message)
        def fade_out():
            self.error_label.configure(text="")
        self.master.after(3000, fade_out)

    def authenticate(self):
        """Handle login authentication"""
        if self.locked_until and time.time() < self.locked_until:
            remaining = int(self.locked_until - time.time())
            self.show_error(f"Account locked. Try again in {remaining} seconds")
            return
        
        if not self.validate_input():
            return
        
        # Simulate loading
        self.login_button.configure(text="Logging in...", state="disabled")
        self.master.update()
        time.sleep(1)
        
        # Placeholder authentication
        if self.username.get() == "user" and self.password.get() == "password":
            self.login_button.configure(text="Success!", bootstyle="success")
            self.master.update()
            time.sleep(0.5)  # Short delay to show success message
            self.on_success()  # Call the success callback
        else:
            self.login_attempts += 1
            if self.login_attempts >= 3:
                self.locked_until = time.time() + 30
                self.show_error("Too many attempts. Account locked for 30 seconds")
            else:
                self.show_error(f"Invalid credentials ({3-self.login_attempts} attempts remaining)")
            self.login_button.configure(text="Login", state="normal")

    def forgot_password_clicked(self):
        """Handle forgot password"""
        dialog = Messagebox.show_info(
            message="Password reset link will be sent to your email",
            title="Reset Password",
            alert=True
        )

    def signup_clicked(self):
        """Handle signup click"""
        dialog = Messagebox.show_info(
            message="Registration feature coming soon!",
            title="Sign Up",
            alert=True
        )

# Example usage:
# if __name__ == "__main__":
#     root = ttk.Window(themename="cosmo")
#     def on_login_success():
#         print("Login successful!")
#         root.destroy()
    
#     app = LoginPortal(root, on_login_success)
#     root.mainloop()