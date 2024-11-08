import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

class PomodoroTimer:
    def __init__(self):
        # Initialize window with modern beige theme
        self.root = ttkb.Window(themename="flatly")
        self.root.title("Pomodoro Timer")
        self.root.geometry("400x400")
        
        self.style = ttkb.Style()
        self.style.configure('TButton', font=('Arial', 14))
        self.style.configure('TLabel', font=('Arial', 14))
        
        # Light beige color palette
        self.bg_color = '#F5F5DC'  # Beige background
        self.fg_color = '#333333'  # Darker text for contrast
        
        # Main Frame with padding
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize timer variables
        self.time_left = 25 * 60  # 25 minutes in seconds
        self.timer_running = False
        
        # Create the UI elements with modern, minimal design
        self.create_ui_elements()
        
        # Set the beige background color for the window and frame
        self.root.configure(bg=self.bg_color)
        self.main_frame.configure(style='Custom.TFrame')
        self.style.configure('Custom.TFrame', background=self.bg_color)

    def create_ui_elements(self):
        # Timer display label, large font for focus
        self.timer_label = ttk.Label(self.main_frame, text="25:00", 
                                     font=('Arial', 72, 'bold'), foreground=self.fg_color,
                                     background=self.bg_color)
        self.timer_label.pack(pady=30)
        
        # Start/Stop button with modern outline style
        self.toggle_button = ttkb.Button(self.main_frame, text="START", 
                                         bootstyle="primary-outline", width=20,
                                         command=self.toggle_timer)
        self.toggle_button.pack(pady=20)

        # Styling for main elements: smooth shadow and hover effect
        self.add_shadow(self.timer_label)
        self.add_shadow(self.toggle_button)

    def add_shadow(self, widget):
        # Optional drop shadow effect for depth (adjust positioning and style)
        shadow = ttkb.Label(self.main_frame, text="", bootstyle="inverse-light")
        shadow.place(in_=widget, x=2, y=2, relwidth=1, relheight=1)
        widget.lift()

    def toggle_timer(self):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.timer_running = True
        self.toggle_button.config(text="STOP")
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False
        self.toggle_button.config(text="START")

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            minutes, seconds = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.time_left -= 1
            self.root.after(1000, self.update_timer)
        elif self.time_left <= 0:
            self.timer_label.config(text="00:00")
            self.stop_timer()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PomodoroTimer()
    app.run()
