import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji

class Dashboard:
    def __init__(self, master, routes):
        self.master = master
        self.master.geometry("800x600")
        self.master.title("Personal Productivity Hub")
        self.routes = routes

        # Create main container with gradient effect
        self.main_container = ttk.Frame(master)
        self.main_container.pack(fill="both", expand=True)

        # Left sidebar for visual appeal
        self.sidebar = ttk.Frame(self.main_container, bootstyle="dark")
        self.sidebar.pack(side="left", fill="y", padx=2)

        # Main content frame
        self.content_frame = ttk.Frame(self.main_container, padding=20)
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Welcome section
        self.create_welcome_section()

        # Modules grid
        self.create_modules_grid()

        # Footer with logout
        self.create_footer()

    def create_welcome_section(self):
        """Create welcome section with greeting and date"""
        welcome_frame = ttk.Frame(self.content_frame)
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Title with decorative elements
        title_frame = ttk.Frame(welcome_frame)
        title_frame.pack(fill="x")

        # Decorative left line
        ttk.Separator(title_frame).pack(side="left", fill="x", expand=True, pady=20)

        # Main title
        title = ttk.Label(
            title_frame,
            text="✨ Productivity Hub ✨",
            font=("SF Mono", 28, "bold"),
            bootstyle="primary",
            padding=(20, 0)
        )
        title.pack(side="left")

        # Decorative right line
        ttk.Separator(title_frame).pack(side="left", fill="x", expand=True, pady=20)

    def create_modules_grid(self):
        """Create grid of module buttons with icons"""
        # Container for module buttons
        modules_frame = ttk.Frame(self.content_frame, padding=10)
        modules_frame.pack(fill="both", expand=True)

        # Configure grid layout
        modules_frame.columnconfigure(0, weight=1)
        modules_frame.columnconfigure(1, weight=1)
        
        # Module definitions with icons
        modules = [
            {
                "name": "To-Doist",
                "icon": "📝",
                "description": "Manage your tasks",
                "style": "info"
            },
            {
                "name": "Pomodoro",
                "icon": "⏰",
                "description": "Focus timer",
                "style": "danger"
            },
            {
                "name": "Stopwatch",
                "icon": "⏱️",
                "description": "Time tracker",
                "style": "warning"
            },
            {
                "name": "NotesHub",
                "icon": "📔",
                "description": "Capture your thoughts",
                "style": "success"
            }
        ]

        # Create module buttons in grid
        for i, module in enumerate(modules):
            # Module container frame
            module_frame = ttk.Frame(
                modules_frame,
                bootstyle=f"{module['style']}-borderless"
            )
            module_frame.grid(
                row=i // 2,
                column=i % 2,
                padx=10,
                pady=10,
                sticky="nsew"
            )

            # Create button with hover effect
            button = ttk.Button(
                module_frame,
                text=f"{module['icon']}  {module['name']}",
                command=lambda m=module['name']: self.open_module(m),
                bootstyle=f"{module['style']}-outline",
                width=25,
                padding=20
            )
            button.pack(expand=True, fill="both")

            # Description label
            desc_label = ttk.Label(
                module_frame,
                text=module['description'],
                bootstyle=f"{module['style']}-inverse",
                font=("SF Mono", 10)
            )
            desc_label.pack(pady=(5, 0))

    def create_footer(self):
        """Create footer with logout button"""
        footer_frame = ttk.Frame(self.content_frame, padding=10)
        footer_frame.pack(fill="x", side="bottom")

        # Separator above footer
        ttk.Separator(footer_frame).pack(fill="x", pady=(0, 10))

        # Logout button
        logout_btn = ttk.Button(
            footer_frame,
            text="🚪 Logout",
            command=self.master.quit,
            bootstyle="danger-outline",
            width=15
        )
        logout_btn.pack(side="right")

    def open_module(self, module_name):
        """Handle module button clicks"""
        route_key = module_name.lower().replace("-", "")
        if route_key in self.routes:
            self.routes[route_key]()

# Example usage
if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    
    # Example routes dictionary
    routes = {
        "todoist": lambda: print("Opening To-Doist..."),
        "pomodoro": lambda: print("Opening Pomodoro..."),
        "stopwatch": lambda: print("Opening Stopwatch..."),
        "noteshub": lambda: print("Opening NotesHub...")
    }
    
    app = Dashboard(root, routes)
    root.mainloop()