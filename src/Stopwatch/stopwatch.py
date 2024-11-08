import tkinter as tk
from tkinter import ttk
import math
import time

class ModernStopwatch:
    def __init__(self, master):
        self.master = master
        self.master.title("Modern Stopwatch")
        self.master.geometry("300x500")
        self.master.configure(bg='#F5F5DC')  # Light beige background

        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0

        self.create_widgets()

    def create_widgets(self):
        # Digital time display
        self.time_var = tk.StringVar(value="00:00.00")
        self.time_label = tk.Label(self.master, textvariable=self.time_var, font=("SF Mono", 40, "bold"),
                                   bg='#EEE8D5', fg='#657B83')  # Softer beige background and darker text
        self.time_label.pack(pady=30)

        # Stopwatch face
        self.canvas = tk.Canvas(self.master, width=250, height=250, bg='#EEE8D5', highlightthickness=0)  # Softer beige background
        self.canvas.pack()

        # Draw stopwatch face
        self.canvas.create_oval(10, 10, 240, 240, outline='#B58900', width=4)  # Golden outline
        for i in range(60):
            angle = i * 6 - 90
            start = 110 if i % 5 == 0 else 115
            x1 = 125 + start * math.cos(math.radians(angle))
            y1 = 125 + start * math.sin(math.radians(angle))
            x2 = 125 + 120 * math.cos(math.radians(angle))
            y2 = 125 + 120 * math.sin(math.radians(angle))
            width = 2 if i % 5 == 0 else 1
            self.canvas.create_line(x1, y1, x2, y2, fill='#B58900', width=width)  # Golden markers

        # Add numbers
        for i in range(0, 60, 5):
            angle = i * 6 - 90
            x = 125 + 95 * math.cos(math.radians(angle))
            y = 125 + 95 * math.sin(math.radians(angle))
            self.canvas.create_text(x, y, text=str(i), font=("SF Mono", 12, "bold"), fill='#657B83')  # Dark gray text

        # Create stopwatch hands
        self.second_hand = self.canvas.create_line(125, 125, 125, 45, width=2, fill='#DC322F')  # Light red for second hand
        self.centisecond_hand = self.canvas.create_line(125, 125, 125, 60, width=1, fill='#CB4B16')  # Orange for centisecond hand

        # Create center circle
        self.canvas.create_oval(120, 120, 130, 130, fill='#B58900')  # Golden center

        # Buttons
        button_frame = tk.Frame(self.master, bg='#EEE8D5')  # Softer beige background for buttons frame
        button_frame.pack(fill='x', pady=20)

        button_style = ttk.Style()
        button_style.configure('TButton', background='#EEE8D5', foreground='#657B83', font=('SF Mono', 10))
        button_style.map('TButton', background=[('active', '#D3D3C0')])

        # Start/Stop button
        self.start_stop_button = tk.Button(self.master, text="▶", command=self.toggle_stopwatch,
                                           font=("SF Mono", 24), bg='#B58900', fg='#FDF6E3',  # Golden button
                                           activebackground='#D3D3C0', activeforeground='#FDF6E3',
                                           relief='flat', width=3, height=1)
        self.start_stop_button.pack(pady=18)

    def toggle_stopwatch(self):
        if self.is_running:
            self.stop_stopwatch()
        else:
            self.start_stopwatch()

    def start_stopwatch(self):
        self.is_running = True
        self.start_time = time.time() - self.elapsed_time
        self.update_stopwatch()
        self.start_stop_button.config(text="■")

    def stop_stopwatch(self):
        self.is_running = False
        self.start_stop_button.config(text="▶")

    def update_stopwatch(self):
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time
            self.update_display(self.elapsed_time)
            self.master.after(10, self.update_stopwatch)  # Update every 10ms for smooth movement

    def update_display(self, elapsed):
        minutes, seconds = divmod(int(elapsed), 60)
        centiseconds = int((elapsed - int(elapsed)) * 100)
        self.time_var.set(f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}")

        # Update second hand
        second_angle = (elapsed % 60) * 6 - 90
        self.update_hand(self.second_hand, second_angle, 100)

        # Update centisecond hand
        centisecond_angle = (elapsed * 100 % 100) * 3.6 - 90
        self.update_hand(self.centisecond_hand, centisecond_angle, 85)

    def update_hand(self, hand, angle, length):
        x = 125 + length * math.cos(math.radians(angle))
        y = 125 + length * math.sin(math.radians(angle))
        self.canvas.coords(hand, 125, 125, x, y)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernStopwatch(root)
    root.mainloop()
