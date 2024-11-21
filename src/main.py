# main.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ToDo.TODO import EnhancedTodoList
from tkinter import messagebox
from Stopwatch.stopwatch import EnhancedStopwatch
from PomodoroTimer.pomodoro import PomodoroTimer
from Dashboard.dashborad import Dashboard
from Login.llogin import LoginPortal
from Flashcard.flash import FlashcardManager
from Flashcard.flash import StudySession

class MainApplication:
    def __init__(self):
        # Create the main window
        self.root = ttk.Window(themename="minty")
        self.root.title("Personal Productivity Hub")
        self.root.geometry("1000x800")

        # Initialize class variables
        self.current_window = None
        self.dashboard = None
        self.routes = {
            "todoist": self.open_todo,
            "stopwatch": self.open_stopwatch,
            "pomodoro": self.open_pomodoro,
            "flashcards": self.open_flashcards,
        }

        # Create login window as the initial view
        self.show_login()

    def show_login(self):
        """Show the login window"""
        # Clear any existing widgets
        if self.current_window:
            self.current_window.destroy()

        # Create a new frame for login
        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        # Create the login portal
        self.login = LoginPortal(self.current_window, self.on_login_success)

    def on_login_success(self):
        """Called when login is successful"""
        print("Login successful! Showing dashboard...")  # Debug print
        self.show_dashboard()

    def show_dashboard(self):
        """Initialize and show the dashboard"""
        print("Showing dashboard...")  # Debug print

        # Destroy current window if it exists
        if self.current_window:
            self.current_window.destroy()

        # Create new frame for dashboard
        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        # Configure grid
        self.current_window.grid_columnconfigure(0, weight=1)
        self.current_window.grid_rowconfigure(0, weight=1)

        # Create dashboard
        try:
            self.dashboard = Dashboard(self.current_window, self.routes)
            print("Dashboard created successfully")  # Debug print
        except Exception as e:
            print(f"Error creating dashboard: {e}")  # Debug print
            raise

    def open_todo(self):
        if self.current_window:
            self.current_window.destroy()

        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        back_button = ttk.Button(
            self.current_window,
            text="← Back to Dashboard",
            command=self.show_dashboard,
            bootstyle="info-outline",
            width=20,
        )
        back_button.pack(pady=10, padx=10, anchor="nw")

        todo_container = ttk.Frame(self.current_window)
        todo_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        todo_app = EnhancedTodoList(todo_container)

    def open_stopwatch(self):
        if self.current_window:
            self.current_window.destroy()

        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        back_button = ttk.Button(
            self.current_window,
            text="← Back to Dashboard",
            command=self.show_dashboard,
            bootstyle="warning-outline",
            width=20,
        )
        back_button.pack(pady=10, padx=10, anchor="nw")

        try:
            stopwatch = EnhancedStopwatch(self.current_window)
        except Exception as e:
            print(f"Error initializing stopwatch: {e}")

    def open_pomodoro(self):
        if self.current_window:
            self.current_window.destroy()

        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        back_button = ttk.Button(
            self.current_window,
            text="← Back to Dashboard",
            command=self.show_dashboard,
            bootstyle="danger-outline",
            width=20,
        )
        back_button.pack(pady=10, padx=10, anchor="nw")

        pomodoro = PomodoroTimer(self.current_window)


    def open_flashcards(self):
        print("Opening Flashcards...")  # Debug print
        if self.current_window:
            self.current_window.destroy()

        self.current_window = ttk.Frame(self.root)
        self.current_window.pack(fill="both", expand=True)

        back_button = ttk.Button(
            self.current_window,
            text="← Back to Dashboard",
            command=self.show_dashboard,
            bootstyle="primary-outline",
            width=20,
        )
        back_button.pack(pady=10, padx=10, anchor="nw")

        try:
            # # Create a new top-level window for the FlashcardManager
            # flashcard_window = ttk.Toplevel(self.root)
            # flashcard_window.title("MindFlow Flashcards")
            # flashcard_window.geometry("900x700")

            # Initialize the FlashcardManager with the new window
            flashcard_app = FlashcardManager(self.current_window)
            print("Flashcard Manager initialized successfully")
        except Exception as e:
            print(f"Error initializing FlashcardManager: {e}")
            messagebox.showerror("Initialization Error", str(e))

    def run(self):
        """Start the application"""
        print("Starting application...")  # Debug print
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
 