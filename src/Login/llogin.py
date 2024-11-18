import tkinter as tk
from typing import Callable, Optional
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tooltip import ToolTip
import re
import json
import bcrypt
from dataclasses import dataclass
from pathlib import Path
import asyncio
import aiofiles
from functools import partial
import logging
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="login_portal.log",
)


@dataclass
class UserCredentials:
    """Data class to store user credentials and settings"""

    username: str
    password_hash: str
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    remember_me: bool = False


class LoginPortal:
    def __init__(
        self,
        master: ttk.Window,
        on_success: Callable,
        theme: str = "minty",
        config_path: str = "config.json",
    ):
        """
        Initialize the LoginPortal with enhanced security and customization options

        Args:
            master: The master window
            on_success: Callback function for successful login
            theme: ttkbootstrap theme name
            config_path: Path to configuration file
        """
        self.master = master
        self.on_success = on_success
        self.config_path = Path(config_path)

        # Initialize configuration
        self.load_config()

        # Setup main UI
        self.setup_ui()
        self.setup_bindings()
        self.load_saved_credentials()

    def run_async(self, coro):
        """Run coroutine in the event loop thread"""

        async def wrapped():
            try:
                await coro
            except Exception as e:
                logging.error(f"Async error: {e}")
                self.master.after(0, lambda: self.show_error("An error occurred"))

        future = asyncio.run_coroutine_threadsafe(wrapped(), self.loop)
        return future

    def start_async_loop(self):
        """Start the async event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def setup_bindings(self) -> None:
        """Setup keyboard bindings with async support"""
        self.master.bind("<Return>", lambda e: self.handle_login())
        self.master.bind("<Escape>", lambda e: self.master.destroy())

        # Start async event loop in separate thread
        # thread = threading.Thread(target=self.start_async_loop, daemon=True)
        # thread.start()

    def handle_login(self) -> None:
        """Synchronous wrapper for the authentication process"""
        username = self.username_var.get()
        password = self.password_var.get()

        if not self.validate_input(username, password):
            return

        # Check for account lockout
        user_data = self.config["users"].get(username, {})
        if user_data.get("locked_until"):
            locked_until = datetime.fromisoformat(user_data["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds
                self.show_error(f"Account locked. Try again in {remaining} seconds")
                return

        # Show loading state
        self.login_button.configure(text="Signing in...", state="disabled")
        self.master.update()

        try:
            # Verify credentials
            if self.verify_credentials(username, password):
                self.handle_successful_login_sync(username)
            else:
                self.handle_failed_login_sync(username)
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            self.show_error("An error occurred. Please try again.")
        finally:
            self.login_button.configure(text="Sign In", state="normal")

    def handle_successful_login_sync(self, username: str) -> None:
        """Synchronous version of successful login handling"""
        # Update user data
        self.config["users"][username]["last_login"] = datetime.now().isoformat()
        self.config["users"][username]["failed_attempts"] = 0

        # Handle remember me
        if self.remember_var.get():
            self.save_credentials(username)

        # Show success message
        self.login_button.configure(text="Success!", bootstyle="success")
        self.master.update()
        self.master.after(500)  # Short delay to show success message

        # Save config and trigger callback
        self.save_config()
        self.on_success()

    def handle_failed_login_sync(self, username: str) -> None:
        """Synchronous version of failed login handling"""
        user_data = self.config["users"].get(username, {"failed_attempts": 0})

        user_data["failed_attempts"] = user_data.get("failed_attempts", 0) + 1

        if user_data["failed_attempts"] >= self.config["max_attempts"]:
            lockout_time = datetime.now() + timedelta(
                seconds=self.config["lockout_duration"]
            )
            user_data["locked_until"] = lockout_time.isoformat()
            self.show_error(
                f"Too many attempts. Account locked for {self.config['lockout_duration']} seconds"
            )
        else:
            remaining = self.config["max_attempts"] - user_data["failed_attempts"]
            self.show_error(f"Invalid credentials ({remaining} attempts remaining)")

        self.config["users"][username] = user_data
        self.save_config()

    async def authenticate(self) -> None:
        """Asynchronously handle login authentication"""
        # Update UI in main thread
        self.master.after(
            0,
            lambda: self.login_button.configure(text="Signing in...", state="disabled"),
        )

        username = self.username_var.get()
        password = self.password_var.get()

        if not self.validate_input(username, password):
            self.master.after(
                0, lambda: self.login_button.configure(text="Sign In", state="normal")
            )
            return

        try:
            # Check for account lockout
            user_data = self.config["users"].get(username, {})
            if user_data.get("locked_until"):
                locked_until = datetime.fromisoformat(user_data["locked_until"])
                if datetime.now() < locked_until:
                    remaining = (locked_until - datetime.now()).seconds
                    self.master.after(
                        0,
                        lambda: self.show_error(
                            f"Account locked. Try again in {remaining} seconds"
                        ),
                    )
                    return

            # Simulate network delay
            await asyncio.sleep(1)

            if self.verify_credentials(username, password):
                await self.handle_successful_login(username)
            else:
                await self.handle_failed_login(username)

        except Exception as e:
            logging.error(f"Authentication error: {e}")
            self.master.after(0, lambda: self.show_error("An error occurred"))

        finally:
            self.master.after(
                0, lambda: self.login_button.configure(text="Sign In", state="normal")
            )

    def cleanup(self):
        """Cleanup resources"""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread_pool.shutdown()

    def load_config(self) -> None:
        """Load configuration from JSON file"""
        default_config = {
            "max_attempts": 3,
            "lockout_duration": 30,
            "min_password_length": 8,
            "remember_me_duration": 7,  # days
            "users": {},
        }

        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.config = default_config

    def save_config(self) -> None:
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def setup_ui(self) -> None:
        """Setup the main UI components with enhanced styling"""
        # Main container with gradient background
        self.container = ttk.Frame(self.master, padding=20)
        self.container.pack(fill=BOTH, expand=YES)

        # Header section
        self.setup_header()

        # Form section
        self.setup_form()

        # Footer section
        self.setup_footer()

    def setup_header(self) -> None:
        """Setup header section with logo and welcome message"""
        header_frame = ttk.Frame(self.container)
        header_frame.pack(fill=X, pady=(0, 20))

        # Logo (can be customized with actual image)
        self.logo = ttk.Label(
            header_frame, text="🔐", font=("SF Pro Display", 48), bootstyle="primary"
        )
        self.logo.pack(pady=(0, 10))

        # Welcome message
        self.welcome_label = ttk.Label(
            header_frame,
            text="Welcome Back",
            font=("SF Pro Display", 24, "bold"),
            bootstyle="primary",
        )
        self.welcome_label.pack()

        self.subtitle = ttk.Label(
            header_frame,
            text="Sign in to continue",
            font=("SF Pro Display", 12),
            bootstyle="secondary",
        )
        self.subtitle.pack()

    def setup_form(self) -> None:
        """Setup the login form with enhanced validation and security"""
        self.form_frame = ttk.Frame(self.container)
        self.form_frame.pack(fill=X, pady=20)

        # Username field
        self.username_var = tk.StringVar()
        self.username_entry = self.create_entry(
            self.form_frame, "Username", self.username_var, "👤"
        )

        # Password field
        self.password_var = tk.StringVar()
        self.password_entry = self.create_entry(
            self.form_frame, "Password", self.password_var, "🔒", show="•"
        )

        # Add show/hide password button
        self.toggle_pwd_btn = ttk.Button(
            self.password_entry,
            text="👁",
            bootstyle="link",
            command=self.toggle_password,
            width=3,
        )
        self.toggle_pwd_btn.pack(side=RIGHT, padx=5)

        # Remember me checkbox
        self.remember_var = tk.BooleanVar()
        self.remember_checkbox = ttk.Checkbutton(
            self.form_frame,
            text="Remember me",
            variable=self.remember_var,
            bootstyle="primary-round-toggle",
        )
        self.remember_checkbox.pack(pady=10)

        # Login button with loading animation
        self.login_button = ttk.Button(
            self.form_frame,
            text="Sign In",
            command=self.handle_login,
            bootstyle="primary",
            width=30,
        )
        self.login_button.pack(pady=(20, 10))

        # Error message
        self.error_label = ttk.Label(
            self.form_frame, text="", bootstyle="danger", font=("SF Pro Display", 12)
        )
        self.error_label.pack(pady=5)

    def setup_footer(self) -> None:
        """Setup footer with additional options"""
        footer_frame = ttk.Frame(self.container)
        footer_frame.pack(fill=X, pady=(20, 0))

        # Forgot password link
        self.forgot_pwd_btn = ttk.Button(
            footer_frame,
            text="Forgot Password?",
            bootstyle="link",
            command=self.forgot_password_clicked,
        )
        self.forgot_pwd_btn.pack(side=LEFT)

        # Sign up link
        self.signup_btn = ttk.Button(
            footer_frame,
            text="Create Account",
            bootstyle="link",
            command=self.signup_clicked,
        )
        self.signup_btn.pack(side=RIGHT)

    def create_entry(
        self,
        parent: ttk.Frame,
        placeholder: str,
        textvariable: tk.StringVar,
        icon: str = "",
        **kwargs,
    ) -> ttk.Frame:
        """Create a styled entry field with icon and placeholder"""
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=10)

        if icon:
            icon_label = ttk.Label(frame, text=icon, font=("SF Pro Display", 14))
            icon_label.pack(side=LEFT, padx=5)

        entry = ttk.Entry(
            frame,
            textvariable=textvariable,
            font=("SF Pro Display", 14),
            bootstyle="primary",
            width=30,
            **kwargs,
        )
        entry.pack(fill=X, padx=5)

        # Add placeholder functionality
        if placeholder:
            entry.insert(0, placeholder)
            entry.bind(
                "<FocusIn>", lambda e: self.on_entry_focus_in(entry, placeholder)
            )
            entry.bind(
                "<FocusOut>", lambda e: self.on_entry_focus_out(entry, placeholder)
            )

        return frame

    async def authenticate(self) -> None:
        """Asynchronously handle login authentication with enhanced security"""
        username = self.username_var.get()
        password = self.password_var.get()

        if not self.validate_input(username, password):
            return

        # Check for account lockout
        user_data = self.config["users"].get(username, {})
        if user_data.get("locked_until"):
            locked_until = datetime.fromisoformat(user_data["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds
                self.show_error(f"Account locked. Try again in {remaining} seconds")
                return

        # Show loading state
        self.login_button.configure(text="Signing in...", state="disabled")
        self.master.update()

        # Simulate network delay
        await asyncio.sleep(1)

        try:
            # In a real application, this would verify against a secure database
            if self.verify_credentials(username, password):
                await self.handle_successful_login(username)
            else:
                await self.handle_failed_login(username)
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            self.show_error("An error occurred. Please try again.")
        finally:
            self.login_button.configure(text="Sign In", state="normal")

    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify user credentials using secure password hashing"""
        user_data = self.config["users"].get(username)
        if not user_data:
            return False

        try:
            stored_hash = user_data["password_hash"].encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
        except Exception as e:
            logging.error(f"Password verification error: {e}")
            return False

    async def handle_successful_login(self, username: str) -> None:
        """Handle successful login attempt"""
        # Update user data
        self.config["users"][username]["last_login"] = datetime.now().isoformat()
        self.config["users"][username]["failed_attempts"] = 0

        # Handle remember me
        if self.remember_var.get():
            self.save_credentials(username)

        # Show success message
        self.login_button.configure(text="Success!", bootstyle="success")
        await asyncio.sleep(0.5)

        # Save config and trigger callback
        self.save_config()
        self.on_success()

    async def handle_failed_login(self, username: str) -> None:
        """Handle failed login attempt with security measures"""
        user_data = self.config["users"].get(username, {"failed_attempts": 0})

        user_data["failed_attempts"] = user_data.get("failed_attempts", 0) + 1

        if user_data["failed_attempts"] >= self.config["max_attempts"]:
            lockout_time = datetime.now() + timedelta(
                seconds=self.config["lockout_duration"]
            )
            user_data["locked_until"] = lockout_time.isoformat()
            self.show_error(
                f"Too many attempts. Account locked for {self.config['lockout_duration']} seconds"
            )
        else:
            remaining = self.config["max_attempts"] - user_data["failed_attempts"]
            self.show_error(f"Invalid credentials ({remaining} attempts remaining)")

        self.config["users"][username] = user_data
        self.save_config()

    def validate_input(self, username: str, password: str) -> bool:
        """Validate user input with enhanced security checks"""
        if username in ("Username", "") or password in ("Password", ""):
            self.show_error("Please enter both username and password")
            return False

        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            self.show_error(
                "Username must be 3-20 characters (letters, numbers, underscore)"
            )
            return False

        if len(password) < self.config["min_password_length"]:
            self.show_error(
                f"Password must be at least {self.config['min_password_length']} characters"
            )
            return False

        return True

    def save_credentials(self, username: str) -> None:
        """Securely save credentials for remember me functionality"""
        try:
            with open(".remember_me", "w") as f:
                json.dump({"username": username}, f)
        except Exception as e:
            logging.error(f"Error saving credentials: {e}")

    def load_saved_credentials(self) -> None:
        """Load saved credentials if remember me was enabled"""
        try:
            if Path(".remember_me").exists():
                with open(".remember_me", "r") as f:
                    data = json.load(f)
                    self.username_var.set(data["username"])
                    self.remember_var.set(True)
        except Exception as e:
            logging.error(f"Error loading saved credentials: {e}")

    def show_error(self, message: str, duration: int = 3000) -> None:
        """Show error message with fade effect"""
        self.error_label.configure(text=message)
        self.master.after(duration, lambda: self.error_label.configure(text=""))

    def setup_bindings(self) -> None:
        """Setup keyboard bindings"""
        self.master.bind("<Return>", lambda e: asyncio.run(self.authenticate()))
        self.master.bind("<Escape>", lambda e: self.master.destroy())

    # Utility methods
    def toggle_password(self) -> None:
        """Toggle password visibility"""
        current = self.password_entry.winfo_children()[0].cget("show")
        self.password_entry.winfo_children()[0].configure(
            show="" if current == "•" else "•"
        )

    def on_entry_focus_in(self, entry: ttk.Entry, placeholder: str) -> None:
        """Handle entry focus in event"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            if placeholder == "Password":
                entry.configure(show="•")

    def on_entry_focus_out(self, entry: ttk.Entry, placeholder: str) -> None:
        """Handle entry focus out event"""
        if entry.get() == "":
            entry.insert(0, placeholder)
            if placeholder == "Password":
                entry.configure(show="")

    def forgot_password_clicked(self) -> None:
        """Handle forgot password request"""
        username = self.username_var.get()
        if username and username != "Username":
            Messagebox.show_info(
                message=f"Password reset instructions sent to email associated with {username}",
                title="Password Reset",
                alert=True,
            )
        else:
            Messagebox.show_warning(
                message="Please enter your username first",
                title="Password Reset",
                alert=True,
            )

    def signup_clicked(self) -> None:
        """Handle signup request with registration form"""
        signup_window = ttk.Toplevel(self.master)
        signup_window.title("Create Account")
        signup_window.geometry("400x500")

        # Registration form
        reg_frame = ttk.Frame(signup_window, padding=20)
        reg_frame.pack(fill=BOTH, expand=YES)

        # Header
        ttk.Label(
            reg_frame,
            text="Create Your Account",
            font=("SF Pro Display", 20, "bold"),
            bootstyle="primary",
        ).pack(pady=(0, 20))

        # Username
        username_var = tk.StringVar()
        username_frame = self.create_entry(reg_frame, "Username", username_var, "👤")

        # Email
        email_var = tk.StringVar()
        email_frame = self.create_entry(reg_frame, "Email", email_var, "📧")

        # Password
        password_var = tk.StringVar()
        password_frame = self.create_entry(
            reg_frame, "Password", password_var, "🔒", show="•"
        )

        # Confirm Password
        confirm_var = tk.StringVar()
        confirm_frame = self.create_entry(
            reg_frame, "Confirm Password", confirm_var, "🔒", show="•"
        )

        # Error label
        error_label = ttk.Label(
            reg_frame, text="", bootstyle="danger", font=("SF Pro Display", 12)
        )
        error_label.pack(pady=5)

        def validate_registration():
            """Validate registration form input"""
            username = username_var.get()
            email = email_var.get()
            password = password_var.get()
            confirm = confirm_var.get()

            # Basic validation
            if username in ("", "Username"):
                error_label.configure(text="Please enter a username")
                return False

            if email in ("", "Email"):
                error_label.configure(text="Please enter an email")
                return False

            if password in ("", "Password"):
                error_label.configure(text="Please enter a password")
                return False

            if confirm in ("", "Confirm Password"):
                error_label.configure(text="Please confirm your password")
                return False

            # Username validation
            if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
                error_label.configure(text="Invalid username format")
                return False

            # Email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                error_label.configure(text="Invalid email format")
                return False

            # Password validation
            if len(password) < self.config["min_password_length"]:
                error_label.configure(
                    text=f"Password must be at least {self.config['min_password_length']} characters"
                )
                return False

            if password != confirm:
                error_label.configure(text="Passwords do not match")
                return False

            # Check if username exists
            if username in self.config["users"]:
                error_label.configure(text="Username already exists")
                return False

            return True

        def handle_registration():
            """Process registration if validation passes"""
            if not validate_registration():
                return

            try:
                # Hash password
                password = password_var.get()
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

                # Create user entry
                self.config["users"][username_var.get()] = {
                    "email": email_var.get(),
                    "password_hash": password_hash.decode("utf-8"),
                    "created_at": datetime.now().isoformat(),
                    "failed_attempts": 0,
                    "last_login": None,
                    "locked_until": None,
                }

                # Save config
                self.save_config()

                # Show success message
                Messagebox.show_info(
                    message="Account created successfully! You can now log in.",
                    title="Registration Successful",
                    alert=True,
                )

                # Close registration window
                signup_window.destroy()

            except Exception as e:
                logging.error(f"Registration error: {e}")
                error_label.configure(text="An error occurred. Please try again.")

        # Register button
        ttk.Button(
            reg_frame,
            text="Create Account",
            command=handle_registration,
            bootstyle="primary",
            width=30,
        ).pack(pady=20)

    def create_password_reset_form(self) -> None:
        """Create password reset form in a new window"""
        reset_window = ttk.Toplevel(self.master)
        reset_window.title("Reset Password")
        reset_window.geometry("400x300")

        # Reset form
        reset_frame = ttk.Frame(reset_window, padding=20)
        reset_frame.pack(fill=BOTH, expand=YES)

        # Header
        ttk.Label(
            reset_frame,
            text="Reset Password",
            font=("SF Pro Display", 20, "bold"),
            bootstyle="primary",
        ).pack(pady=(0, 20))

        # Email entry
        email_var = tk.StringVar()
        email_frame = self.create_entry(reset_frame, "Email", email_var, "📧")

        def handle_reset():
            """Process password reset request"""
            email = email_var.get()

            if email in ("", "Email"):
                Messagebox.show_warning(
                    message="Please enter your email address",
                    title="Reset Password",
                    alert=True,
                )
                return

            # In a real application, this would send a reset link
            Messagebox.show_info(
                message="If an account exists with this email, "
                "you will receive password reset instructions shortly.",
                title="Reset Password",
                alert=True,
            )
            reset_window.destroy()

        # Reset button
        ttk.Button(
            reset_frame,
            text="Send Reset Link",
            command=handle_reset,
            bootstyle="primary",
            width=30,
        ).pack(pady=20)


def create_login_portal(on_success: Callable, theme: str = "cosmo") -> None:
    """Create and run a login portal instance with proper cleanup"""
    root = ttk.Window(themename=theme)
    root.title("Login Portal")
    root.geometry("400x600")

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    app = LoginPortal(root, on_success)
    root.mainloop()


# Example usage:
if __name__ == "__main__":

    def on_successful_login():
        print("Login successful!")

    create_login_portal(on_successful_login)
