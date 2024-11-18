import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import MessageDialog
from datetime import datetime, timedelta
import json
from tkinter import messagebox
from typing import Optional, Dict, List
import uuid


class Task:
    def __init__(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        priority: str = "Medium",
        status: str = "Pending",
    ):

        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        task = cls(data["title"])
        task.id = data["id"]
        task.description = data["description"]
        task.due_date = data["due_date"]
        task.priority = data["priority"]
        task.status = data["status"]
        task.created_at = data["created_at"]
        task.completed_at = data["completed_at"]
        return task


class EnhancedTodoList:
    def __init__(self, master):
        self.master = master
        self.is_root_window = isinstance(master, ttk.Window)

        # Only set title if master is a root window
        if self.is_root_window:
            self.master.title("Enhanced ToDoist")

        self.tasks: List[Task] = []
        self.setup_styles()
        self.create_layout()
        self.load_tasks()
        self.update_view()

    def setup_styles(self):
        """Configure application styles and themes"""
        self.style = ttk.Style()
        self.style.configure(
            "Task.Treeview",
            rowheight=40,
            font=("Segoe UI", 10),
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        self.style.configure(
            "Task.Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#E0E0E0"
        )

        # Priority color tags
        self.tree_tags = {
            "high": "#E74C3C",
            "medium": "#2980B9",
            "low": "#7F8C8D",
            "completed": "#27AE60",
        }

    def create_layout(self):
        """Create the main application layout"""
        # Main container with padding
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=BOTH, expand=YES)

        # Header with title
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=X, pady=(0, 10))

        if not self.is_root_window:  # Only add the title label if we're in a frame
            ttk.Label(
                header_frame,
                text="Enhanced ToDoist",
                font=("Segoe UI", 24, "bold"),
                bootstyle="inverse-primary",
            ).pack(side=LEFT)

        ttk.Button(
            header_frame,
            text="Add Task",
            bootstyle="success-outline",
            command=lambda: self.show_task_dialog(),
        ).pack(side=RIGHT)

        # Create Treeview for tasks
        self.create_task_tree()

        # Action buttons
        self.create_action_buttons()

        # Filter frame
        self.create_filters()

    # Rest of the class remains the same...

    def create_task_tree(self):
        """Create and configure the task treeview"""
        columns = ("id", "title", "priority", "due_date", "status")
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=columns,
            show="headings",
            style="Task.Treeview",
            height=15,
        )

        # Configure columns
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Task")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("due_date", text="Due Date")
        self.tree.heading("status", text="Status")

        # Hide ID column
        self.tree.column("id", width=0, stretch=NO)
        self.tree.column("title", width=300)
        self.tree.column("priority", width=100, anchor=CENTER)
        self.tree.column("due_date", width=150, anchor=CENTER)
        self.tree.column("status", width=100, anchor=CENTER)

        for tag, color in self.tree_tags.items():
            self.tree.tag_configure(tag, foreground=color)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.main_frame, orient=VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Bind double-click event for task details
        self.tree.bind(
            "<Double-1>", lambda e: self.show_task_dialog(self.get_selected_task())
        )

    def create_action_buttons(self):
        """Create action buttons frame"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=X, pady=10)

        ttk.Button(
            button_frame,
            text="Complete",
            bootstyle="success-outline",
            command=self.complete_task,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Delete",
            bootstyle="danger-outline",
            command=self.delete_task,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Statistics",
            bootstyle="info-outline",
            command=self.show_statistics,
        ).pack(side=RIGHT, padx=5)

    def create_filters(self):
        """Create filtering options"""
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filters", padding=10)
        filter_frame.pack(fill=X, pady=10)

        # Status filter
        self.status_var = ttk.StringVar(value="All")
        ttk.Label(filter_frame, text="Status:").pack(side=LEFT, padx=5)
        status_cb = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=["All", "Pending", "Completed"],
            width=10,
        )
        status_cb.pack(side=LEFT, padx=5)

        # Priority filter
        self.priority_var = ttk.StringVar(value="All")
        ttk.Label(filter_frame, text="Priority:").pack(side=LEFT, padx=5)
        priority_cb = ttk.Combobox(
            filter_frame,
            textvariable=self.priority_var,
            values=["All", "High", "Medium", "Low"],
            width=10,
        )
        priority_cb.pack(side=LEFT, padx=5)

        # Bind filter changes
        status_cb.bind("<<ComboboxSelected>>", lambda e: self.update_view())
        priority_cb.bind("<<ComboboxSelected>>", lambda e: self.update_view())

    def get_selected_task(self) -> Optional[Task]:
        """Get the currently selected task"""
        selected = self.tree.selection()
        if not selected:
            return None

        task_id = self.tree.item(selected[0])["values"][0]
        return next((task for task in self.tasks if task.id == task_id), None)

    # Update the show_task_dialog method to properly use Querybox
    def show_task_dialog(self, task: Optional[Task] = None):
        """Show dialog for adding or editing a task"""
        dialog_title = "Edit Task" if task else "New Task"

        # Create custom dialog instead of using Querybox
        details_dialog = ttk.Toplevel(self.master)
        details_dialog.title(dialog_title)
        details_dialog.geometry("400x300")

        # Center the dialog
        details_dialog.update_idletasks()
        width = details_dialog.winfo_width()
        height = details_dialog.winfo_height()
        x = (details_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (details_dialog.winfo_screenheight() // 2) - (height // 2)
        details_dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Create form
        form_frame = ttk.Frame(details_dialog, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)

        # Title
        ttk.Label(form_frame, text="Title:").pack(anchor=W)
        title_entry = ttk.Entry(form_frame)
        title_entry.pack(fill=X, pady=(0, 10))
        if task:
            title_entry.insert(0, task.title)

        # Description
        ttk.Label(form_frame, text="Description:").pack(anchor=W)
        description_text = ttk.Text(form_frame, height=3, width=40)
        description_text.pack(fill=X, pady=(0, 10))
        if task:
            description_text.insert("1.0", task.description)

        # Due Date
        ttk.Label(form_frame, text="Due Date (YYYY-MM-DD):").pack(anchor=W)
        due_date_entry = ttk.Entry(form_frame)
        due_date_entry.pack(fill=X, pady=(0, 10))
        if task and task.due_date:
            due_date_entry.insert(0, task.due_date)

        # Priority
        ttk.Label(form_frame, text="Priority:").pack(anchor=W)
        priority_var = ttk.StringVar(value=task.priority if task else "Medium")
        priority_combo = ttk.Combobox(
            form_frame,
            textvariable=priority_var,
            values=["High", "Medium", "Low"],
            state="readonly",
        )
        priority_combo.pack(fill=X, pady=(0, 20))

        def save_task():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Invalid Input", "Task title cannot be empty!")
                return

            if task:  # Editing existing task
                task.title = title
                task.description = description_text.get("1.0", "end-1c")
                task.due_date = due_date_entry.get()
                task.priority = priority_var.get()
            else:  # Creating new task
                new_task = Task(
                    title=title,
                    description=description_text.get("1.0", "end-1c"),
                    due_date=due_date_entry.get(),
                    priority=priority_var.get(),
                )
                self.tasks.append(new_task)

            self.save_tasks()
            self.update_view()
            details_dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=X, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Cancel",
            bootstyle="secondary",
            command=details_dialog.destroy,
        ).pack(side=RIGHT, padx=5)

        ttk.Button(
            button_frame, text="Save", bootstyle="primary", command=save_task
        ).pack(side=RIGHT)

        # Make dialog modal
        details_dialog.transient(self.master)
        details_dialog.grab_set()
        self.master.wait_window(details_dialog)

    def complete_task(self):
        """Mark selected task as completed"""
        task = self.get_selected_task()
        if not task:
            messagebox.showwarning("No Selection", "Please select a task to complete")
            return

        task.status = "Completed"
        task.completed_at = datetime.now().isoformat()
        self.save_tasks()
        self.update_view()

    def delete_task(self):
        """Delete selected task"""
        task = self.get_selected_task()
        if not task:
            messagebox.showwarning("No Selection", "Please select a task to delete")
            return

        if messagebox.askyesno(
            "Confirm Delete", "Are you sure you want to delete this task?"
        ):
            self.tasks.remove(task)
            self.save_tasks()
            self.update_view()

    def show_statistics(self):
        """Show task statistics"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == "Completed"])
        pending = total - completed

        high_priority = len([t for t in self.tasks if t.priority == "High"])
        overdue = len(
            [
                t
                for t in self.tasks
                if t.due_date
                and datetime.fromisoformat(t.due_date) < datetime.now()
                and t.status != "Completed"
            ]
        )

        stats = f"""Task Statistics:
        Total Tasks: {total}
        Completed: {completed}
        Pending: {pending}
        High Priority: {high_priority}
        Overdue: {overdue}
        
        Completion Rate: {(completed/total*100 if total else 0):.1f}%
        """

        messagebox.showinfo("Statistics", stats)

    def update_view(self):
        """Update the task tree view with filtered tasks"""
        self.tree.delete(*self.tree.get_children())

        status_filter = self.status_var.get()
        priority_filter = self.priority_var.get()

        for task in self.tasks:
            if (status_filter == "All" or task.status == status_filter) and (
                priority_filter == "All" or task.priority == priority_filter
            ):

                values = (
                    task.id,
                    task.title,
                    task.priority,
                    task.due_date or "No due date",
                    task.status,
                )

                tags = []
                tags.append(task.priority.lower())
                if task.status == "Completed":
                    tags = ["completed"]

                self.tree.insert("", END, values=values, tags=tags)

    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            with open("enhanced_tasks.json", "r") as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(task_data) for task_data in data]
        except FileNotFoundError:
            self.tasks = []
        except json.JSONDecodeError:
            messagebox.showerror(
                "Error", "Task file is corrupted. Starting with empty task list."
            )
            self.tasks = []

    def save_tasks(self):
        """Save tasks to JSON file"""
        with open("enhanced_tasks.json", "w") as f:
            json.dump([task.to_dict() for task in self.tasks], f, indent=2)


if __name__ == "__main__":
    root = ttk.Window(themename="morph")
    app = EnhancedTodoList(root)
    root.mainloop()
