import tkinter as tk
import queue
import logging

class TaskDisplay:
    def __init__(self, todo_list):
        self.root = tk.Tk()
        self.root.title("Task List")
        self.root.geometry("800x600")  # Set a bigger screen size
        self.root.configure(bg='#1e1e1e')  # Set dark mode background color

        self.text_widget = tk.Text(self.root, wrap='word', font=('Helvetica', 16), bg='#1e1e1e', fg='#ffffff', insertbackground='white', padx=20, pady=20, spacing1=3, spacing3=3)
        self.text_widget.pack(expand=1, fill='both')

        self.tasks = []
        self.task_queue = queue.Queue()
        self.todo_list = todo_list
        self.root.bind('`', self.handle_down_arrow)
        self.root.after(100, self.check_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def handle_down_arrow(self, event):
        self.text_widget.delete("insert-1c", "insert")
        self.text_widget.insert(tk.INSERT, "✅")

    def update_tasks(self, tasks=None):
        if tasks is None:
            tasks = self.todo_list.get_tasks()
        logging.info(f"Updating tasks in GUI: {tasks}")
        formatted_tasks = [{"task": task["task"], "completed": task["completed"]} for task in tasks]
        self.task_queue.put(formatted_tasks)

    def check_queue(self):
        try:
            while True:
                tasks = self.task_queue.get_nowait()  # Non-blocking
                self.tasks = tasks
                self._update_text_widget(tasks)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)  # Check the queue every 100 ms

    def _update_text_widget(self, tasks):
        self.text_widget.delete(1.0, tk.END)
        if tasks:
            for i, task in enumerate(tasks):
                task_text = f"{i+1}. {task['task']}"
                if task.get('completed', False):
                    task_text += " ✅"
                self.text_widget.insert(tk.END, f"{task_text}\n")
        else:
            self.text_widget.insert(tk.END, "Your to-do list is empty.")

    def run(self):
        self.root.mainloop()
    
    def hide(self):
        self.root.withdraw()

    def on_close(self):
        # Process tasks when the GUI is closed
        current_tasks = self.text_widget.get(1.0, tk.END).strip().split("\n")
        current_tasks = [task.split(". ", 1)[1] for task in current_tasks if ". " in task]
        existing_tasks = self.todo_list.get_tasks()

        # Add new tasks and mark completed tasks
        for task in current_tasks:
            if task.endswith("✅"):
                task_name = task[:-1].strip()
                if not any(t['task'] == task_name for t in existing_tasks):
                    self.todo_list.add_task(task_name)
                self.todo_list.complete_task(task_name)
            else:
                task_name = task.strip()
                if not any(t['task'] == task_name for t in existing_tasks):
                    self.todo_list.add_task(task_name)
                else:
                    # If task is in the database but not marked as complete in the text, unmark it
                    if any(t['task'] == task_name and t['completed'] for t in existing_tasks):
                        self.todo_list.uncomplete_task(task_name)

        # Remove tasks that are no longer in the list, excluding completed tasks
        for task in existing_tasks:
            if task['task'] not in [t.split(" ✅")[0].strip() for t in current_tasks]:
                self.todo_list.remove_task(task['task'])

        # Update the task queue with the latest tasks
        self.update_tasks()

        self.root.withdraw()  # Hide the GUI instead of destroying it