import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import json
import os
from plyer import notification
import threading
from PIL import Image, ImageTk


class PomodoroTimer:
    def __init__(self, master):
        self.master = master
        self.settings = self.load_settings()

        # Timer states and configurations
        self.timer_states = {
            "pomodoro": self.settings["pomodoro_time"] * 60,
            "short_break": self.settings["short_break"] * 60,
            "long_break": self.settings["long_break"] * 60,
        }
        self.current_state = "pomodoro"
        self.time_left = self.timer_states["pomodoro"]
        self.timer_running = False
        self.pomodoros_completed = 0

        # Statistics tracking
        self.stats = self.load_statistics()

        self.create_ui()

    def create_ui(self):
        # Main container
        self.container = ttk.Frame(self.master, padding="20")
        self.container.pack(fill=BOTH, expand=YES)

        # Timer type selection
        self.timer_frame = ttk.Frame(self.container)
        self.timer_frame.pack(fill=X, pady=(0, 20))

        self.timer_buttons = []
        for timer_type in ["Pomodoro", "Short Break", "Long Break"]:
            btn = ttk.Button(
                self.timer_frame,
                text=timer_type,
                bootstyle="info-outline",
                command=lambda t=timer_type.lower().replace(
                    " ", "_"
                ): self.switch_timer(t),
            )
            btn.pack(side=LEFT, padx=5, expand=YES)
            self.timer_buttons.append(btn)

        # Timer display
        self.timer_display = ttk.Label(
            self.container,
            text=self.format_time(self.time_left),
            font=("SF Pro Display", 72, "bold"),
            bootstyle="info",
        )
        self.timer_display.pack(pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.container,
            maximum=self.timer_states[self.current_state],
            value=self.time_left,
            length=300,
            bootstyle="info-striped",
        )
        self.progress.pack(fill=X, pady=10)

        # Control buttons frame
        self.control_frame = ttk.Frame(self.container)
        self.control_frame.pack(fill=X, pady=20)

        # Start/Stop button
        self.toggle_button = ttk.Button(
            self.control_frame,
            text="Start",
            command=self.toggle_timer,
            bootstyle="info",
            width=15,
        )
        self.toggle_button.pack(side=LEFT, padx=5)

        # Reset button
        self.reset_button = ttk.Button(
            self.control_frame,
            text="Reset",
            command=self.reset_timer,
            bootstyle="info-outline",
            width=15,
        )
        self.reset_button.pack(side=LEFT, padx=5)

        # Settings button
        self.settings_button = ttk.Button(
            self.control_frame,
            text="⚙",
            command=self.show_settings,
            bootstyle="info-outline",
            width=3,
        )
        self.settings_button.pack(side=RIGHT, padx=5)

        # Statistics frame
        self.stats_frame = ttk.Labelframe(
            self.container, text="Today's Statistics", padding=10
        )
        self.stats_frame.pack(fill=X, pady=20)

        self.stats_labels = {}
        stats_items = [
            ("Pomodoros Completed", "completed"),
            ("Total Focus Time", "focus_time"),
            ("Current Streak", "streak"),
        ]

        for i, (label_text, stat_key) in enumerate(stats_items):
            frame = ttk.Frame(self.stats_frame)
            frame.pack(fill=X, pady=2)

            ttk.Label(frame, text=label_text + ":", bootstyle="info").pack(side=LEFT)
            self.stats_labels[stat_key] = ttk.Label(frame, text="0", bootstyle="info")
            self.stats_labels[stat_key].pack(side=RIGHT)

        self.update_stats_display()

    def switch_timer(self, timer_type):
        self.current_state = timer_type
        self.time_left = self.timer_states[timer_type]
        self.reset_timer()

    def toggle_timer(self):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.timer_running = True
        self.toggle_button.config(text="Stop")
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False
        self.toggle_button.config(text="Start")

    def reset_timer(self):
        self.stop_timer()
        self.time_left = self.timer_states[self.current_state]
        self.update_display()

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.master.after(1000, self.update_timer)
        elif self.time_left <= 0:
            self.timer_complete()

    def timer_complete(self):
        self.stop_timer()
        if self.current_state == "pomodoro":
            self.pomodoros_completed += 1
            self.update_statistics()

        # Show notification
        threading.Thread(target=self.show_notification).start()

        # Auto-switch to break or back to pomodoro
        if self.current_state == "pomodoro":
            if self.pomodoros_completed % 4 == 0:
                self.switch_timer("long_break")
            else:
                self.switch_timer("short_break")
        else:
            self.switch_timer("pomodoro")

    def show_notification(self):
        title = (
            "Pomodoro Complete!"
            if self.current_state == "pomodoro"
            else "Break Complete!"
        )
        message = (
            "Time for a break!"
            if self.current_state == "pomodoro"
            else "Time to focus!"
        )

        notification.notify(
            title=title,
            message=message,
            app_icon=None,  # Add path to your icon if available
            timeout=10,
        )

    def update_display(self):
        self.timer_display.config(text=self.format_time(self.time_left))
        self.progress.config(value=self.time_left)

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def load_settings(self):
        default_settings = {
            "pomodoro_time": 25,
            "short_break": 5,
            "long_break": 15,
            "auto_start_breaks": True,
            "auto_start_pomodoros": True,
            "notifications_enabled": True,
        }

        try:
            with open("pomodoro_settings.json", "r") as f:
                return {**default_settings, **json.load(f)}
        except FileNotFoundError:
            return default_settings

    def save_settings(self):
        with open("pomodoro_settings.json", "w") as f:
            json.dump(self.settings, f)

    def load_statistics(self):
        today = datetime.now().date().isoformat()
        default_stats = {"date": today, "completed": 0, "focus_time": 0, "streak": 0}

        try:
            with open("pomodoro_stats.json", "r") as f:
                stats = json.load(f)
                if stats["date"] != today:
                    stats = default_stats
                return stats
        except FileNotFoundError:
            return default_stats

    def update_statistics(self):
        self.stats["completed"] += 1
        self.stats["focus_time"] += self.settings["pomodoro_time"]
        self.save_statistics()
        self.update_stats_display()

    def save_statistics(self):
        with open("pomodoro_stats.json", "w") as f:
            json.dump(self.stats, f)

    def update_stats_display(self):
        self.stats_labels["completed"].config(text=str(self.stats["completed"]))
        hours = self.stats["focus_time"] // 60
        minutes = self.stats["focus_time"] % 60
        self.stats_labels["focus_time"].config(text=f"{hours}h {minutes}m")
        self.stats_labels["streak"].config(text=str(self.stats["streak"]))

    def show_settings(self):
        settings_window = ttk.Toplevel(self.master)
        settings_window.title("Pomodoro Settings")
        settings_window.geometry("400x500")

        settings_frame = ttk.Frame(settings_window, padding=20)
        settings_frame.pack(fill=BOTH, expand=YES)

        # Time settings
        time_frame = ttk.Labelframe(
            settings_frame, text="Timer Duration (minutes)", padding=10
        )
        time_frame.pack(fill=X, pady=10)

        time_settings = [
            ("Pomodoro:", "pomodoro_time"),
            ("Short Break:", "short_break"),
            ("Long Break:", "long_break"),
        ]

        for label, key in time_settings:
            frame = ttk.Frame(time_frame)
            frame.pack(fill=X, pady=5)

            ttk.Label(frame, text=label).pack(side=LEFT)
            spinbox = ttk.Spinbox(
                frame, from_=1, to=60, width=10, value=self.settings[key]
            )
            spinbox.pack(side=RIGHT)

        # Autostart settings
        auto_frame = ttk.Labelframe(settings_frame, text="Automatic Timers", padding=10)
        auto_frame.pack(fill=X, pady=10)

        ttk.Checkbutton(
            auto_frame,
            text="Auto-start breaks",
            variable=ttk.BooleanVar(value=self.settings["auto_start_breaks"]),
        ).pack(fill=X, pady=5)

        ttk.Checkbutton(
            auto_frame,
            text="Auto-start pomodoros",
            variable=ttk.BooleanVar(value=self.settings["auto_start_pomodoros"]),
        ).pack(fill=X, pady=5)

        # Notification settings
        notif_frame = ttk.Labelframe(settings_frame, text="Notifications", padding=10)
        notif_frame.pack(fill=X, pady=10)

        ttk.Checkbutton(
            notif_frame,
            text="Enable notifications",
            variable=ttk.BooleanVar(value=self.settings["notifications_enabled"]),
        ).pack(fill=X, pady=5)

        # Save button
        ttk.Button(
            settings_frame,
            text="Save Settings",
            command=lambda: self.save_and_close_settings(settings_window),
            bootstyle="info",
        ).pack(pady=20)

    def save_and_close_settings(self, settings_window):
        # Save settings logic here
        settings_window.destroy()
        self.load_settings()  # Reload settings
        self.reset_timer()  # Reset timer with new settings
