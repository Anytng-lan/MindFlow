# main_app.py
import ttkbootstrap as ttk
from Login.login import LoginPortal
from Dashboard.dashborad import Dashboard
from Stopwatch.stopwatch import ModernStopwatch  # Include other modules here

class App:
    def __init__(self, master):
        self.master = master
        self.show_login_screen()

    def show_login_screen(self):
        LoginPortal(self.master, on_success=self.show_dashboard)

    def show_dashboard(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        routes = {
            "stopwatch": self.show_stopwatch,
            "calendar": self.show_calendar,
            "tasks": self.show_tasks,
            "notes": self.show_notes,
            "analytics": self.show_analytics,
        }
        Dashboard(self.master, routes)

    def show_stopwatch(self):
        self.clear_screen()
        ModernStopwatch(self.master)

    def show_calendar(self):
        # Initialize and show Calendar module
        pass

    def show_tasks(self):
        # Initialize and show Task Manager module
        pass

    def show_notes(self):
        # Initialize and show Notes module
        pass

    def show_analytics(self):
        # Initialize and show Analytics module
        pass

    def clear_screen(self):
        for widget in self.master.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")  # Elegant dark theme
    app = App(root)
    root.mainloop()
