import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import json

class ModernTodoListApp(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")  # Initialize with a valid base theme

        self.title("To-Do List")
        self.geometry("450x600")

        # Custom color scheme
        self.style.configure('TLabel', font=("Segoe UI", 12))
        self.style.configure('TButton', font=("Segoe UI", 10))
        self.style.configure('Accent.TButton', font=("Segoe UI", 10, "bold"))

        # Apply custom styles directly without creating a new theme
        self.style.configure("TLabel", foreground="#5D4037")
        self.style.configure("TButton", background="#FFAB91", foreground="#5D4037")
        self.style.configure("Treeview", background="#FFF3E0", fieldbackground="#FFF3E0", foreground="#5D4037")
        self.style.configure("Treeview.Heading", background="#FFAB91", foreground="#5D4037")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.create_widgets()
        self.load_tasks()

    def create_widgets(self):
        # Header
        header_frame = tb.Frame(self, bootstyle="light")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)

        tb.Label(header_frame, text="ToDoist", font=("Segoe UI", 24, "bold"), bootstyle="inverse-light").grid(row=0, column=0, sticky="w", padx=20, pady=10)

        # Task input area
        input_frame = tb.Frame(self)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20)
        input_frame.columnconfigure(0, weight=1)

        self.task_input = tb.Entry(input_frame, font=("Segoe UI", 12), width=30)
        self.task_input.grid(row=0, column=0, sticky="ew")
        self.task_input.insert(0, "Enter your task here...")  # Placeholder text
        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)

        tb.Button(input_frame, text="Add", command=self.add_task, bootstyle="success").grid(row=0, column=1, padx=(10, 0))

        # Task list
        self.task_tree = ttk.Treeview(self, columns=("Task", "Status"), show="headings", selectmode="browse")
        self.task_tree.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.task_tree.heading("Task", text="Task")
        self.task_tree.heading("Status", text="Status")
        self.task_tree.column("Task", width=300)
        self.task_tree.column("Status", width=100, anchor="center")

        # Configure tag for completed tasks
        self.task_tree.tag_configure("completed", foreground="green")

        # Scrollbar for task list
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.task_tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tb.Frame(self)
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.columnconfigure((0, 1, 2), weight=1)

        tb.Button(button_frame, text="Mark Done", bootstyle="success", command=self.mark_done).grid(row=0, column=0, padx=5)
        tb.Button(button_frame, text="Delete", bootstyle="danger", command=self.delete_task).grid(row=0, column=1, padx=5)
        tb.Button(button_frame, text="View Stats", bootstyle="info", command=self.view_stats).grid(row=0, column=2, padx=5)

    def add_task(self):
        task = self.task_input.get().strip()  # Strip any leading/trailing spaces
        if task and task != "Enter your task here...":  # Prevent adding placeholder as task
            self.task_tree.insert("", "end", values=(task, "Pending"))
            self.task_input.delete(0, "end")  # Clear the input field after adding
            self.save_tasks()
        else:
            messagebox.showwarning("Invalid Task", "Please enter a valid task.")

    def mark_done(self):
        selected_item = self.task_tree.selection()
        if selected_item:
            self.task_tree.set(selected_item, "Status", "Completed")
            self.task_tree.item(selected_item, tags=("completed",))
            self.save_tasks()
        else:
            messagebox.showwarning("No Selection", "Please select a task to mark as done.")

    def delete_task(self):
        selected_item = self.task_tree.selection()
        if selected_item:
            self.task_tree.delete(selected_item)
            self.save_tasks()
        else:
            messagebox.showwarning("No Selection", "Please select a task to delete.")

    def view_stats(self):
        total_count = len(self.task_tree.get_children())
        done_count = len([item for item in self.task_tree.get_children() if self.task_tree.item(item)["values"][1] == "Completed"])
        messagebox.showinfo("Task Statistics", f"Total tasks: {total_count}\nCompleted tasks: {done_count}")

    def clear_placeholder(self, event):
        if self.task_input.get() == "Enter your task here...":
            self.task_input.delete(0, "end")

    def restore_placeholder(self, event):
        if self.task_input.get() == "":
            self.task_input.insert(0, "Enter your task here...")

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                data = json.load(f)
                for task in data:
                    text = task.get("text", "")
                    status = task.get("status", "Pending")
                    self.task_tree.insert("", "end", values=(text, status))
                    if status == "Completed":
                        self.task_tree.item(self.task_tree.get_children()[-1], tags=("completed",))
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            messagebox.showerror("Error", "The tasks file is corrupted. Starting with an empty task list.")

    def save_tasks(self):
        data = []
        for item in self.task_tree.get_children():
            text, status = self.task_tree.item(item)["values"]
            data.append({"text": text, "status": status})
        with open("tasks.json", "w") as f:
            json.dump(data, f)

if __name__ == '__main__':
    app = ModernTodoListApp()
    app.mainloop()
