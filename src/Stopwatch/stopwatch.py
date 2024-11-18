import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tooltip import ToolTip
import math
import time
import json
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
import threading
import sqlite3
from typing import Callable, Dict, List, Optional
import logging


class EnhancedStopwatch(ttk.Frame):
    """A professional stopwatch widget with advanced features and elegant UI."""

    def load_settings(self) -> dict:
        """Load settings from JSON file."""
        settings_path = Path("stopwatch_settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading settings: {e}")

        return self._get_default_settings()

    def _get_default_settings(self) -> dict:
        """Get default settings."""
        return {
            "clock_bg_color": "#ffffff",
            "second_hand_color": "#ff4444",
            "millisecond_hand_color": "#4444ff",
            "marker_color": "#222222",
            "center_dot_color": "#222222",
            "clock_border_color": "#000000",
            "precision": 2,
            "auto_save": True,
            "theme_mode": "light",
            "export_format": "CSV",
        }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.pack(fill="both", expand=True)

        # Initialize logging
        self._setup_logging()

        # Initialize variables
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.lap_times: List[float] = []
        self.split_times: List[float] = []
        self.last_lap_time = 0
        self.timer_thread: Optional[threading.Thread] = None
        self.precision = 2
        self.auto_save = True
        self.theme_mode = "light"

        # Load settings and initialize database
        self.settings = self.load_settings()
        self.init_database()

        # Event callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_stop": [],
            "on_reset": [],
            "on_lap": [],
            "on_theme_change": [],
            "on_precision_change": [],
        }

        # Create UI elements
        self.create_widgets()
        self.create_lap_table()
        self.apply_theme()

        # Bind keyboard shortcuts
        self._bind_shortcuts()

        # Load last session if auto-save is enabled
        # if self.auto_save:
        #     self.load_last_session()

    def toggle_stopwatch(self):
        """Toggle the stopwatch between running and stopped states."""
        if self.is_running:
            self.stop_stopwatch()
        else:
            self.start_stopwatch()

    def start_stopwatch(self):
        """Start the stopwatch."""
        if not self.is_running:
            self.is_running = True
            if not self.start_time:
                self.start_time = time.time() - self.elapsed_time
            else:
                self.start_time = time.time() - self.elapsed_time

            # Update UI
            self.start_stop_button.configure(text="Stop", bootstyle="danger")
            self.status_indicator.configure(bootstyle="success")

            # Start the update thread
            self.timer_thread = threading.Thread(target=self._update_time, daemon=True)
            self.timer_thread.start()

            # Trigger callbacks
            for callback in self.callbacks["on_start"]:
                callback()

    def stop_stopwatch(self):
        """Stop the stopwatch."""
        if self.is_running:
            self.is_running = False
            self.elapsed_time = time.time() - self.start_time

            # Update UI
            self.start_stop_button.configure(text="Start", bootstyle="success")
            self.status_indicator.configure(bootstyle="danger")

            # Trigger callbacks
            for callback in self.callbacks["on_stop"]:
                callback()

    def reset_stopwatch(self):
        """Reset the stopwatch to zero."""
        self.stop_stopwatch()
        self.elapsed_time = 0
        self.start_time = 0
        self.lap_times.clear()
        self.split_times.clear()
        self.last_lap_time = 0

        # Update displays
        self.time_var.set("00:00:00.00")
        self.lap_var.set("Current Lap: 00:00:00.00")
        self._update_statistics()

        # Clear lap table
        for widget in self.lap_frame.winfo_children():
            widget.destroy()

        # Trigger callbacks
        for callback in self.callbacks["on_reset"]:
            callback()

    def record_lap(self):
        """Record a lap time."""
        if self.is_running:
            current_time = time.time() - self.start_time
            lap_time = current_time - self.last_lap_time

            self.lap_times.append(lap_time)
            self.split_times.append(current_time)
            self.last_lap_time = current_time

            # Add lap to table
            self._add_lap_to_table(len(self.lap_times), lap_time, current_time)

            # Update statistics
            self._update_statistics()

            # Trigger callbacks
            for callback in self.callbacks["on_lap"]:
                callback()

    def _update_time(self):
        """Update the time display continuously."""
        while self.is_running:
            current_time = time.time() - self.start_time
            self._update_display(current_time)
            time.sleep(0.01)  # Small delay to prevent high CPU usage

    def _update_display(self, current_time):
        """Update the time display and clock hands."""
        if not self.is_running:
            return

        # Update digital display
        self.time_var.set(self._format_time(current_time))

        # Update current lap display
        current_lap_time = current_time - self.last_lap_time
        self.lap_var.set(f"Current Lap: {self._format_time(current_lap_time)}")

        # Update clock hands
        self._update_clock_hands(current_time)

    def _format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS.XX format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:0{self.precision + 3}.{self.precision}f}"

    def _update_clock_hands(self, current_time):
        """Update the position of clock hands."""
        # Calculate angles
        seconds_angle = (current_time % 60) * 6 - 90
        milliseconds_angle = (current_time * 1000 % 1000) * 0.36 - 90

        # Update second hand
        x = 100 + 80 * math.cos(math.radians(seconds_angle))
        y = 100 + 80 * math.sin(math.radians(seconds_angle))
        self.canvas.coords(self.second_hand, 100, 100, x, y)

        # Update millisecond hand
        x = 100 + 60 * math.cos(math.radians(milliseconds_angle))
        y = 100 + 60 * math.sin(math.radians(milliseconds_angle))
        self.canvas.coords(self.millisecond_hand, 100, 100, x, y)

    def _update_statistics(self):
        """Update statistics display."""
        if self.lap_times:
            self.stats_vars["best_lap"].set(self._format_time(min(self.lap_times)))
            self.stats_vars["average_lap"].set(
                self._format_time(sum(self.lap_times) / len(self.lap_times))
            )
            self.stats_vars["worst_lap"].set(self._format_time(max(self.lap_times)))
            self.stats_vars["total_laps"].set(str(len(self.lap_times)))
            self.stats_vars["total_time"].set(self._format_time(sum(self.lap_times)))

            if len(self.lap_times) > 1:
                import numpy as np

                std_dev = np.std(self.lap_times)
                self.stats_vars["std_deviation"].set(self._format_time(std_dev))

            # Calculate current pace (average of last 3 laps)
            recent_laps = (
                self.lap_times[-3:] if len(self.lap_times) >= 3 else self.lap_times
            )
            current_pace = sum(recent_laps) / len(recent_laps)
            self.stats_vars["current_pace"].set(self._format_time(current_pace))

    def _add_lap_to_table(self, lap_number: int, lap_time: float, split_time: float):
        """Add a new lap to the lap table."""
        lap_frame = ttk.Frame(self.lap_frame)
        lap_frame.pack(fill="x", padx=5, pady=2)

        # Lap number
        ttk.Label(lap_frame, text=f"{lap_number}", width=5).pack(
            side="left", expand=True
        )

        # Lap time
        ttk.Label(lap_frame, text=self._format_time(lap_time), width=12).pack(
            side="left", expand=True
        )

        # Split time
        ttk.Label(lap_frame, text=self._format_time(split_time), width=12).pack(
            side="left", expand=True
        )

        # Total time
        ttk.Label(
            lap_frame, text=self._format_time(sum(self.lap_times)), width=12
        ).pack(side="left", expand=True)

        # Pace (compared to average)
        avg_pace = sum(self.lap_times) / len(self.lap_times)
        pace_diff = lap_time - avg_pace
        pace_text = f"{'+' if pace_diff > 0 else ''}{self._format_time(pace_diff)}"
        ttk.Label(lap_frame, text=pace_text, width=12).pack(side="left", expand=True)

    def _setup_logging(self):
        """Initialize logging configuration."""
        self.logger = logging.getLogger("EnhancedStopwatch")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler("stopwatch.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def init_database(self):
        """Initialize SQLite database for storing sessions."""
        self.db_path = Path("stopwatch_sessions.db")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    total_time REAL,
                    lap_times TEXT,
                    split_times TEXT
                )
            """
            )

    def create_widgets(self):
        """Create all UI widgets with modern styling."""
        # Main container
        self.main_container = ttk.Frame(self, padding="10")
        self.main_container.pack(fill="both", expand=True)

        # Create sections
        self.create_top_section()
        self.create_middle_section()
        self.create_bottom_section()
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create a menu bar with additional functionality."""
        self.menu_bar = ttk.Menu(self)

        # File menu
        file_menu = ttk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self.export_data)

        # View menu
        view_menu = ttk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(
            label="Dark Mode",
            command=self.toggle_theme,
            variable=tk.BooleanVar(value=self.theme_mode == "dark"),
        )

        # Settings menu
        settings_menu = ttk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_settings)

        # Help menu
        help_menu = ttk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)

        if isinstance(self.winfo_toplevel(), tk.Tk):
            self.winfo_toplevel().config(menu=self.menu_bar)

    def create_top_section(self):
        """Create the top section with time display and current lap."""
        top_frame = ttk.Frame(self.main_container)
        top_frame.pack(fill="x", pady=(0, 10))

        # Status indicator
        self.status_frame = ttk.Frame(top_frame, padding=2)
        self.status_frame.pack(fill="x")

        self.status_indicator = ttk.Label(
            self.status_frame, text="●", font=("JetBrains Mono", 12), bootstyle="danger"
        )
        self.status_indicator.pack(side="right")

        # Main time display
        self.time_var = tk.StringVar(value="00:00:00.00")
        self.time_label = ttk.Label(
            top_frame,
            textvariable=self.time_var,
            font=("JetBrains Mono", 48, "bold"),
            bootstyle="info",
        )
        self.time_label.pack(pady=5)

        # Lap time display with shadow effect
        self.lap_var = tk.StringVar(value="Current Lap: 00:00:00.00")
        # shadow_label = ttk.Label(
        #     top_frame,
        #     textvariable=self.lap_var,
        #     font=("JetBrains Mono", 16),
        #     bootstyle="secondary",
        #     foreground="#666666"
        # )
        # shadow_label.pack()
        # shadow_label.place(relx=0.502, rely=0.502)

        self.lap_label = ttk.Label(
            top_frame,
            textvariable=self.lap_var,
            font=("JetBrains Mono", 16),
            bootstyle="secondary",
        )
        self.lap_label.pack()

    def create_middle_section(self):
        """Create the middle section with analog clock and statistics."""
        middle_frame = ttk.Frame(self.main_container)
        middle_frame.pack(fill="x", pady=10)

        # Analog clock
        self.create_clock_face(middle_frame)

        # Enhanced statistics panel
        self.create_enhanced_stats_panel(middle_frame)

    def create_clock_face(self, parent):
        """Create an elegant analog clock face."""
        clock_frame = ttk.LabelFrame(parent, text="Analog Display", padding=10)
        clock_frame.pack(side="left", padx=10)

        self.canvas = tk.Canvas(
            clock_frame,
            width=200,
            height=200,
            bg=self.settings.get("clock_bg_color", "#ffffff"),
            highlightthickness=0,
        )
        self.canvas.pack()

        self.draw_clock_face()

        # Create clock hands
        self.create_clock_hands()

    def create_clock_hands(self):
        """Create elegant clock hands with smooth animations."""
        # Second hand with gradient effect
        self.second_hand = self.canvas.create_line(
            100,
            100,
            100,
            20,
            width=2,
            fill=self.settings.get("second_hand_color", "#ff4444"),
            smooth=True,
        )

        # Millisecond hand
        self.millisecond_hand = self.canvas.create_line(
            100,
            100,
            100,
            30,
            width=1,
            fill=self.settings.get("millisecond_hand_color", "#4444ff"),
            smooth=True,
        )

        # Decorative center
        self.canvas.create_oval(
            95,
            95,
            105,
            105,
            fill=self.settings.get("center_dot_color", "#222222"),
            outline=self.settings.get("clock_border_color", "#000000"),
            width=2,
        )

    def draw_clock_face(self):
        """Draw an elegant clock face with markers."""
        # Draw hour markers
        for i in range(12):
            angle = i * 30 - 90
            start_x = 100 + 85 * math.cos(math.radians(angle))
            start_y = 100 + 85 * math.sin(math.radians(angle))
            end_x = 100 + 95 * math.cos(math.radians(angle))
            end_y = 100 + 95 * math.sin(math.radians(angle))

            self.canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                width=2,
                fill=self.settings.get("marker_color", "#222222"),
            )

        # Draw minute markers
        for i in range(60):
            if i % 5 != 0:  # Skip positions where hour markers are
                angle = i * 6 - 90
                start_x = 100 + 90 * math.cos(math.radians(angle))
                start_y = 100 + 90 * math.sin(math.radians(angle))
                end_x = 100 + 95 * math.cos(math.radians(angle))
                end_y = 100 + 95 * math.sin(math.radians(angle))

                self.canvas.create_line(
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                    width=1,
                    fill=self.settings.get("marker_color", "#222222"),
                )

    def create_enhanced_stats_panel(self, parent):
        """Create an enhanced statistics panel with graphs."""
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=10)
        stats_frame.pack(side="right", fill="both", expand=True, padx=10)

        # Statistics variables with more metrics
        self.stats_vars = {
            "best_lap": tk.StringVar(value="--:--:--"),
            "average_lap": tk.StringVar(value="--:--:--"),
            "worst_lap": tk.StringVar(value="--:--:--"),
            "total_laps": tk.StringVar(value="0"),
            "total_time": tk.StringVar(value="00:00:00.00"),
            "std_deviation": tk.StringVar(value="--:--:--"),
            "current_pace": tk.StringVar(value="--:--:--"),
        }

        # Create statistics labels with tooltips
        for label_text, var_key in [
            ("Best Lap", "best_lap"),
            ("Average Lap", "average_lap"),
            ("Worst Lap", "worst_lap"),
            ("Total Laps", "total_laps"),
            ("Total Time", "total_time"),
            ("Std Deviation", "std_deviation"),
            ("Current Pace", "current_pace"),
        ]:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill="x", pady=2)

            label = ttk.Label(frame, text=f"{label_text}:", font=("JetBrains Mono", 10))
            label.pack(side="left")

            value_label = ttk.Label(
                frame,
                textvariable=self.stats_vars[var_key],
                font=("JetBrains Mono", 10, "bold"),
                bootstyle="info",
            )
            value_label.pack(side="right")

            ToolTip(label, text=f"Shows the {label_text.lower()}")

    def create_bottom_section(self):
        """Create the bottom section with controls and lap table."""
        bottom_frame = ttk.Frame(self.main_container)
        bottom_frame.pack(fill="x", pady=10)

        # Main controls
        self.create_control_buttons(bottom_frame)

        # Utility controls
        self.create_utility_buttons(bottom_frame)

    def create_control_buttons(self, parent):
        """Create main control buttons with icons."""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(pady=5)

        button_configs = [
            {
                "text": "Start",
                "icon": "play",
                "style": "success",
                "command": self.toggle_stopwatch,
                "tooltip": "Space",
                "width": 12,
            },
            {
                "text": "Lap",
                "icon": "flag",
                "style": "info",
                "command": self.record_lap,
                "tooltip": "Enter",
                "width": 12,
            },
            {
                "text": "Reset",
                "icon": "arrow-counterclockwise",
                "style": "danger",
                "command": self.reset_stopwatch,
                "tooltip": "R",
                "width": 12,
            },
        ]

        for config in button_configs:
            btn = ttk.Button(
                controls_frame,
                text=config["text"],
                bootstyle=config["style"],
                width=config["width"],
                command=config["command"],
            )
            btn.pack(side="left", padx=5)

            ToolTip(btn, text=f"{config['tooltip']} to {config['text']}")

            if config["text"] == "Start":
                self.start_stop_button = btn
            elif config["text"] == "Lap":
                self.lap_button = btn
            elif config["text"] == "Reset":
                self.reset_button = btn

    def create_utility_buttons(self, parent):
        """Create utility buttons with advanced features."""
        utils_frame = ttk.Frame(parent)
        utils_frame.pack(pady=5)

        utility_configs = [
            {
                "text": "Settings",
                "icon": "gear",
                "style": "info-outline",
                "command": self.show_settings,
                "tooltip": "Configure stopwatch settings",
                "width": 12,
            },
            {
                "text": "Analysis",
                "icon": "graph",
                "style": "info-outline",
                "command": self.show_analysis,
                "tooltip": "View detailed analysis",
                "width": 12,
            },
        ]

        for config in utility_configs:
            btn = ttk.Button(
                utils_frame,
                text=config["text"],
                bootstyle=config["style"],
                width=config["width"],
                command=config["command"],
            )
            btn.pack(side="left", padx=5)
            ToolTip(btn, text=config["tooltip"])

            if config["text"] == "Export":
                self.export_button = btn

    def create_lap_table(self):
        """Create an enhanced lap time table with sorting capabilities."""
        self.lap_frame = ScrolledFrame(self.main_container, autohide=True, height=150)
        self.lap_frame.pack(fill="both", expand=True, pady=10)

        # Enhanced table headers with sorting
        headers_frame = ttk.Frame(self.lap_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)

        headers = [
            ("№", "number"),
            ("Lap Time", "lap"),
            ("Split Time", "split"),
            ("Total Time", "total"),
            ("Pace", "pace"),
        ]

        for header, sort_key in headers:
            header_btn = ttk.Button(
                headers_frame,
                text=header,
                bootstyle="link",
                command=lambda k=sort_key: self.sort_laps(k),
            )
            header_btn.pack(side="left", expand=True)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts with enhanced functionality."""
        shortcuts = {
            "<space>": self.toggle_stopwatch,
            "<Return>": self.record_lap,
            "<r>": self.reset_stopwatch,
            "<Control-s>": self.export_data,
            # '<Control-z>': self.undo_last_lap,
            # '<Control-q>': self.quit_application,
            "<F1>": self.show_shortcuts,
            "<Control-p>": self.show_settings,
        }

        for key, command in shortcuts.items():
            self.bind_all(key, lambda e, cmd=command: cmd())

    def show_settings(self):
        """Show settings dialog with enhanced configuration options."""
        settings_window = ttk.Toplevel(self)
        settings_window.title("Stopwatch Settings")
        settings_window.geometry("400x500")

        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # General settings
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="General")

        # Appearance settings
        appearance_frame = ttk.Frame(notebook, padding=10)
        notebook.add(appearance_frame, text="Appearance")

        # Advanced settings
        advanced_frame = ttk.Frame(notebook, padding=10)
        notebook.add(advanced_frame, text="Advanced")

        self._create_general_settings(general_frame)
        self._create_appearance_settings(appearance_frame)
        self._create_advanced_settings(advanced_frame)

    def _create_general_settings(self, parent):
        """Create general settings controls."""
        # Precision setting
        ttk.Label(parent, text="Time Precision:").pack(anchor="w", pady=5)
        precision_var = tk.IntVar(value=self.precision)
        precision_scale = ttk.Scale(
            parent,
            from_=0,
            to=3,
            variable=precision_var,
            command=lambda v: self.update_precision(int(float(v))),
        )
        precision_scale.pack(fill="x", pady=5)

        # Auto-save setting
        auto_save_var = tk.BooleanVar(value=self.auto_save)
        auto_save_check = ttk.Checkbutton(
            parent,
            text="Auto-save sessions",
            variable=auto_save_var,
            command=lambda: self.toggle_auto_save(auto_save_var.get()),
        )
        auto_save_check.pack(anchor="w", pady=5)

    def _create_appearance_settings(self, parent):
        """Create appearance settings controls."""
        # Theme selection
        ttk.Label(parent, text="Theme:").pack(anchor="w", pady=5)
        themes = ["light", "dark", "system"]
        theme_var = tk.StringVar(value=self.theme_mode)
        for theme in themes:
            ttk.Radiobutton(
                parent,
                text=theme.capitalize(),
                value=theme,
                variable=theme_var,
                command=lambda: self.change_theme(theme_var.get()),
            ).pack(anchor="w")

        # Color customization
        ttk.Label(parent, text="Colors:").pack(anchor="w", pady=(15, 5))
        color_options = [
            ("Clock Background", "clock_bg_color"),
            ("Second Hand", "second_hand_color"),
            ("Millisecond Hand", "millisecond_hand_color"),
            ("Markers", "marker_color"),
        ]

        for label, key in color_options:
            frame = ttk.Frame(parent)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text=label).pack(side="left")
            ttk.Button(
                frame, text="Choose", command=lambda k=key: self.choose_color(k)
            ).pack(side="right")

    def _create_advanced_settings(self, parent):
        """Create advanced settings controls."""
        # Export format selection
        ttk.Label(parent, text="Export Format:").pack(anchor="w", pady=5)
        formats = ["CSV", "JSON", "Excel"]
        format_var = tk.StringVar(value=self.settings.get("export_format", "CSV"))
        for fmt in formats:
            ttk.Radiobutton(
                parent,
                text=fmt,
                value=fmt,
                variable=format_var,
                command=lambda: self.update_export_format(format_var.get()),
            ).pack(anchor="w")

        # Database location
        ttk.Label(parent, text="Database Location:").pack(anchor="w", pady=(15, 5))
        db_frame = ttk.Frame(parent)
        db_frame.pack(fill="x", pady=5)
        ttk.Entry(db_frame, textvariable=tk.StringVar(value=str(self.db_path))).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(db_frame, text="Browse", command=self.change_db_location).pack(
            side="right"
        )

    def show_analysis(self):
        """Show detailed analysis window with graphs and statistics."""
        analysis_window = ttk.Toplevel(self)
        analysis_window.title("Lap Time Analysis")
        analysis_window.geometry("600x400")

        # Create tabs for different analyses
        notebook = ttk.Notebook(analysis_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Lap time distribution
        self._create_lap_distribution(notebook)

        # Trend analysis
        self._create_trend_analysis(notebook)

        # Statistics summary
        self._create_statistics_summary(notebook)

    def _create_lap_distribution(self, notebook):
        """Create lap time distribution graph."""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Distribution")

        if self.lap_times:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            fig, ax = plt.subplots()
            ax.hist(self.lap_times, bins=20, edgecolor="black")
            ax.set_title("Lap Time Distribution")
            ax.set_xlabel("Time (seconds)")
            ax.set_ylabel("Frequency")

            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_data(self):
        """Export session data in various formats."""
        if not self.lap_times:
            messagebox.showwarning("No Data", "No lap times to export.")
            return

        export_format = self.settings.get("export_format", "CSV")
        file_types = {
            "CSV": (".csv", "*.csv"),
            "JSON": (".json", "*.json"),
            "Excel": (".xlsx", "*.xlsx"),
        }

        file_path = filedialog.asksaveasfilename(
            defaultextension=file_types[export_format][0],
            filetypes=[(export_format, file_types[export_format][1])],
        )

        if file_path:
            data = self._prepare_export_data()

            try:
                if export_format == "CSV":
                    pd.DataFrame(data).to_csv(file_path, index=False)
                elif export_format == "JSON":
                    pd.DataFrame(data).to_json(file_path, orient="records")
                else:  # Excel
                    pd.DataFrame(data).to_excel(file_path, index=False)

                messagebox.showinfo(
                    "Success", f"Data exported successfully to {file_path}"
                )

            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")

    def _prepare_export_data(self):
        """Prepare data for export."""
        return [
            {
                "lap_number": i + 1,
                "lap_time": self.lap_times[i],
                "split_time": self.split_times[i],
                "total_time": sum(self.lap_times[: i + 1]),
                "timestamp": datetime.fromtimestamp(
                    self.start_time + self.split_times[i]
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for i in range(len(self.lap_times))
        ]

    def save_session(self):
        """Save current session to database."""
        if not self.lap_times:
            messagebox.showwarning("No Data", "No lap times to save.")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO sessions (
                        start_time,
                        end_time,
                        total_time,
                        lap_times,
                        split_times
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        datetime.fromtimestamp(self.start_time).isoformat(),
                        datetime.fromtimestamp(time.time()).isoformat(),
                        sum(self.lap_times),
                        json.dumps(self.lap_times),
                        json.dumps(self.split_times),
                    ),
                )
            messagebox.showinfo("Success", "Session saved successfully!")
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")
            messagebox.showerror("Save Error", f"Error saving session: {str(e)}")

    def load_session(self):
        """Load a previous session from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT start_time, total_time, lap_times, split_times
                    FROM sessions
                    ORDER BY start_time DESC
                """
                )
                sessions = cursor.fetchall()

            if not sessions:
                messagebox.showinfo("No Sessions", "No saved sessions found.")
                return

            # Create session selection dialog
            session_window = ttk.Toplevel(self)
            session_window.title("Load Session")
            session_window.geometry("400x300")

            def load_selected_session():
                selection = session_list.curselection()
                if not selection:
                    return

                session = sessions[selection[0]]
                self.reset_stopwatch()
                self.start_time = datetime.fromisoformat(session[0]).timestamp()
                self.lap_times = json.loads(session[2])
                self.split_times = json.loads(session[3])
                self.elapsed_time = sum(self.lap_times)

                # Update display
                self._update_display(self.elapsed_time)
                self._update_statistics()

                # Recreate lap table
                for i, (lap_time, split_time) in enumerate(
                    zip(self.lap_times, self.split_times)
                ):
                    self._add_lap_to_table(i + 1, lap_time, split_time)

                session_window.destroy()
                messagebox.showinfo("Success", "Session loaded successfully!")

            # Create session list
            session_list = tk.Listbox(session_window)
            session_list.pack(fill="both", expand=True, padx=10, pady=10)

            for session in sessions:
                start_time = datetime.fromisoformat(session[0])
                total_time = session[1]
                session_list.insert(
                    tk.END,
                    f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Total Time: {self._format_time(total_time)}",
                )

            ttk.Button(
                session_window,
                text="Load Selected Session",
                command=load_selected_session,
            ).pack(pady=10)

        except Exception as e:
            self.logger.error(f"Error loading session: {e}")
            messagebox.showerror("Load Error", f"Error loading session: {str(e)}")

    def save_settings(self):
        """Save current settings to JSON file."""
        settings_path = Path("stopwatch_settings.json")
        try:
            with open(settings_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Settings Error", f"Error saving settings: {str(e)}")

    def apply_theme(self):
        """Apply the current theme to all widgets."""
        style = ttk.Style()

        if self.theme_mode == "dark":
            style.configure(".", background="#333333", foreground="#ffffff")
            style.configure("TLabel", background="#333333", foreground="#ffffff")
            style.configure("TButton", background="#444444")
            self.canvas.configure(bg="#222222")
        else:
            style.configure(".", background="#ffffff", foreground="#000000")
            style.configure("TLabel", background="#ffffff", foreground="#000000")
            style.configure("TButton", background="#f0f0f0")
            self.canvas.configure(bg="#ffffff")

    def toggle_theme(self):
        """Toggle between light and dark theme modes."""
        if self.theme_mode == "light":
            self.theme_mode = "dark"
        else:
            self.theme_mode = "light"
        self.apply_theme()

        # Trigger theme change callbacks if any
        for callback in self.callbacks["on_theme_change"]:
            callback()

    def show_about(self):
        """Show about dialog."""
        about_text = """Enhanced Stopwatch v2.0
            
    A professional stopwatch application with advanced features:
    • High-precision timing
    • Lap time tracking
    • Statistical analysis
    • Data export
    • Customizable appearance
    • Keyboard shortcuts
            
    Created with ♥ using Python and tkinter"""

        messagebox.showinfo("About Enhanced Stopwatch", about_text)

    def show_shortcuts(self):
        """Show keyboard shortcuts help."""
        shortcuts_text = """
    Keyboard Shortcuts:
    Space - Start/Stop
    Enter - Record Lap
    R - Reset
    Ctrl+S - Export Data
    Ctrl+Z - Undo Last Lap
    Ctrl+P - Settings
    F1 - Show This Help
    Ctrl+Q - Quit
    """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)


# # Example usage:
# if __name__ == "__main__":
#     root = ttk.Window("Enhanced Stopwatch")
#     stopwatch = EnhancedStopwatch(root)
#     stopwatch.pack(fill="both", expand=True)
#     root.mainloop()
