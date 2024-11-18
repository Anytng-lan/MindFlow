import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.dialogs import Messagebox
from datetime import datetime
import time
from typing import Dict, Callable
import platform


class Dashboard:
    def __init__(self, master: ttk.Frame, routes: Dict[str, Callable]):
        self.master = master
        self.routes = routes
        self.animations = []  # Store animation IDs

        # Create responsive layout
        self.setup_layout()
        self.create_sidebar()
        self.create_content()

        # Start update loops
        self.start_time_update()
        self.check_system_resources()

    def setup_layout(self) -> None:
        """Initialize responsive grid layout"""
        self.master.grid_columnconfigure(1, weight=1)  # Content area expands
        self.master.grid_rowconfigure(0, weight=1)

        # Main container with gradient background
        self.container = ttk.Frame(self.master)
        self.container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

    def create_sidebar(self) -> None:
        """Create animated sidebar with system info and quick actions"""
        self.sidebar = ttk.Frame(self.container, bootstyle="dark")
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(2, 0))

        # System info section
        self.system_frame = ttk.LabelFrame(
            self.sidebar, text="System Info", bootstyle="primary", padding=10
        )
        self.system_frame.pack(fill="x", padx=5, pady=5)

        # Time and date display
        self.time_label = ttk.Label(
            self.system_frame, font=("SF Mono", 12), bootstyle="primary"
        )
        self.time_label.pack(fill="x", pady=2)

        # System metrics
        self.metrics_label = ttk.Label(
            self.system_frame, font=("SF Mono", 10), bootstyle="secondary"
        )
        self.metrics_label.pack(fill="x", pady=2)

        # Quick actions
        actions_frame = ttk.LabelFrame(
            self.sidebar, text="Quick Actions", bootstyle="primary", padding=10
        )
        actions_frame.pack(fill="x", padx=5, pady=5)

        # Quick action buttons
        actions = [
            ("🔄 Refresh", self.refresh_dashboard),
            ("⚙️ Settings", self.show_settings),
            ("❓ Help", self.show_help),
            ("🚪 Logout", self.confirm_logout),
        ]

        for text, command in actions:
            btn = ttk.Button(
                actions_frame,
                text=text,
                command=command,
                bootstyle="primary-outline",
                width=15,
            )
            btn.pack(fill="x", pady=2)
            # Add tooltips
            ToolTip(btn, text=f"Click to {text.split()[-1]}")

    def create_content(self) -> None:
        """Create main content area with welcome message and module grid"""
        # Content container
        self.content = ttk.Frame(self.container, padding=20)
        self.content.grid(row=0, column=1, sticky="nsew")

        # Welcome section with animation
        self.create_welcome_section()

        # Module grid with enhanced visuals
        self.create_module_grid()

        # Status bar
        self.create_status_bar()

    def create_welcome_section(self) -> None:
        """Create animated welcome section"""
        welcome_frame = ttk.Frame(self.content)
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Animated title
        self.title = ttk.Label(
            welcome_frame,
            text="✨ Productivity Hub ✨",
            font=("SF Mono", 28, "bold"),
            bootstyle="primary",
        )
        self.title.pack(pady=10)

        # Start title animation
        self.animate_title()

    def create_module_grid(self) -> None:
        """Create enhanced module grid with animations and metrics"""
        modules_frame = ttk.Frame(self.content)
        modules_frame.pack(fill="both", expand=True)

        # Configure grid
        for i in range(2):
            modules_frame.grid_columnconfigure(i, weight=1)

        # Module definitions
        self.modules = [
            {
                "name": "To-Doist",
                "icon": "📝",
                "description": "Task Management",
                "metrics": "5 tasks due today",
                "style": "info",
                "route": "todoist",
            },
            {
                "name": "Pomodoro",
                "icon": "⏰",
                "description": "Focus Timer",
                "metrics": "2 sessions completed",
                "style": "danger",
                "route": "pomodoro",
            },
            {
                "name": "Stopwatch",
                "icon": "⏱️",
                "description": "Time Tracking",
                "metrics": "Total: 2h 15m today",
                "style": "warning",
                "route": "stopwatch",
            },
            {
                "name": "NotesHub",
                "icon": "📔",
                "description": "Note Taking",
                "metrics": "3 notes created today",
                "style": "success",
                "route": "noteshub",
            },
        ]

        # Create module cards
        for i, module in enumerate(self.modules):
            self.create_module_card(modules_frame, module, i)

    def create_module_card(self, parent: ttk.Frame, module: dict, index: int) -> None:
        """Create individual module card with hover effects and metrics"""
        # Card container - using regular Frame without outline style
        card = ttk.Frame(parent)
        card.grid(row=index // 2, column=index % 2, padx=10, pady=10, sticky="nsew")

        # Add a border using LabelFrame
        card_border = ttk.LabelFrame(card, text="", bootstyle=module["style"])
        card_border.pack(fill="both", expand=True)

        # Module header
        header = ttk.Frame(card_border)
        header.pack(fill="x", padx=10, pady=5)

        # Icon and title
        ttk.Label(
            header,
            text=f"{module['icon']} {module['name']}",
            font=("SF Mono", 16, "bold"),
            bootstyle=module["style"],
        ).pack(side="left")

        # Metrics badge
        ttk.Label(
            header,
            text=module["metrics"],
            bootstyle=f"{module['style']}-inverse",
            padding=(5, 2),
        ).pack(side="right")

        # Description
        ttk.Label(
            card_border,
            text=module["description"],
            bootstyle="secondary",
            font=("SF Mono", 12),
        ).pack(padx=10, pady=5)

        # Action button
        btn = ttk.Button(
            card_border,
            text="Open Module",
            command=lambda: self.open_module(module["route"]),
            bootstyle=f"{module['style']}-outline",
            width=20,
        )
        btn.pack(padx=10, pady=10)

        # Add hover effect
        self.bind_hover_events(card_border, module["style"])

    def create_status_bar(self) -> None:
        """Create status bar with system metrics"""
        self.status_bar = ttk.Frame(self.container)
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Status labels
        self.status_labels = []
        for _ in range(3):
            label = ttk.Label(
                self.status_bar, font=("SF Mono", 10), bootstyle="secondary"
            )
            label.pack(side="left", padx=10)
            self.status_labels.append(label)

    # Utility methods
    def bind_hover_events(self, widget: ttk.Frame, style: str) -> None:
        """Add hover effects to widgets"""

        def on_enter(e):
            widget.configure(bootstyle=f"{style}")

        def on_leave(e):
            widget.configure(bootstyle=style)  # Remove -outline suffix

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def animate_title(self) -> None:
        """Animate dashboard title using after() method"""
        self.title_state = True  # Track animation state

        def toggle_stars():
            if not hasattr(self, "title_state"):  # Check if widget still exists
                return

            stars = "✨" if self.title_state else "💫"
            self.title.configure(text=f"{stars} Productivity Hub {stars}")
            self.title_state = not self.title_state

            # Schedule next animation frame
            animation_id = self.master.after(1000, toggle_stars)
            self.animations.append(animation_id)

        # Start the animation
        toggle_stars()

    def start_time_update(self) -> None:
        """Start real-time clock update"""

        def update_time():
            if not hasattr(self, "time_label"):  # Check if widget still exists
                return

            current_time = datetime.now().strftime("%H:%M:%S")
            current_date = datetime.now().strftime("%B %d, %Y")
            self.time_label.configure(text=f"🕒 {current_time}\n📅 {current_date}")
            # Schedule next update
            animation_id = self.master.after(1000, update_time)
            self.animations.append(animation_id)

        update_time()

    def check_system_resources(self) -> None:
        """Monitor and update system resource usage"""
        try:
            import psutil

            def update_metrics():
                if not hasattr(self, "metrics_label"):  # Check if widget still exists
                    return

                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                self.metrics_label.configure(text=f"CPU: {cpu}%\nMemory: {memory}%")
                # Schedule next update
                animation_id = self.master.after(5000, update_metrics)
                self.animations.append(animation_id)

            update_metrics()
        except ImportError:
            self.metrics_label.configure(text="System metrics unavailable")

    # Action handlers
    def open_module(self, route: str) -> None:
        """Handle module navigation with transition effect"""
        if route in self.routes:
            # Add transition effect here if desired
            self.routes[route]()

    def refresh_dashboard(self) -> None:
        """Refresh dashboard data"""
        # Simulate refresh
        self.master.configure(cursor="watch")
        self.master.after(1000, lambda: self.master.configure(cursor=""))

        # Update metrics
        self.check_system_resources()

    def show_settings(self) -> None:
        """Show settings dialog"""
        Messagebox.show_info("Settings feature coming soon!", "Settings")

    def show_help(self) -> None:
        """Show help dialog"""
        Messagebox.show_info(
            "Need help? Contact support@productivityhub.com", "Help & Support"
        )

    def confirm_logout(self) -> None:
        """Show logout confirmation"""
        if Messagebox.show_question(
            "Are you sure you want to logout?", "Confirm Logout"
        ):
            self.master.quit()

    def __del__(self) -> None:
        """Cleanup method to stop animations"""
        try:
            for animation_id in self.animations:
                self.master.after_cancel(animation_id)
            self.animations.clear()
        except Exception:
            pass  # Handle case where widgets are already destroyed
