from datetime import date
import logging
from Database.Base import Database

class ToDoList:
    def __init__(self):
        self.db = Database()

    def add_task(self, task, task_date=date.today()):
        query = "INSERT INTO todo_list (task, completed, date) VALUES (%s, %s, %s)"
        task = task.strip().lower()  # Normalize task name
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task, False, task_date))
                conn.commit()
                logging.info(f"Task '{task}' added successfully for date {task_date}.")
        except Exception as e:
            logging.error(f"Failed to add task: {e}")
            raise

    def remove_task(self, task, task_date=date.today()):
        query = "DELETE FROM todo_list WHERE task = %s AND date = %s"
        task = task.strip().lower()  # Normalize task name
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task, task_date))
                conn.commit()
                if cursor.rowcount > 0:
                    logging.info(f"Task '{task}' removed successfully for date {task_date}.")
                    return True
                else:
                    logging.info(f"Task '{task}' not found for date {task_date}.")
                    return False
        except Exception as e:
            logging.error(f"Failed to remove task: {e}")
            raise

    def get_tasks(self, task_date=date.today()):
        query = "SELECT task, completed FROM todo_list WHERE date = %s"
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_date,))
                tasks = cursor.fetchall()
                logging.info(f"Tasks retrieved successfully for date {task_date}.")
                return [{"task": task, "completed": completed} for task, completed in tasks]
        except Exception as e:
            logging.error(f"Failed to retrieve tasks: {e}")
            raise
        
    def complete_task(self, task, task_date=date.today()):
        query = "UPDATE todo_list SET completed = %s WHERE task = %s AND date = %s"
        task = task.strip().lower()  # Normalize task name
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (True, task, task_date))
                conn.commit()
                logging.info(f"Task '{task}' marked as completed for date {task_date}.")
        except Exception as e:
            logging.error(f"Failed to complete task: {e}")
            raise

    def uncomplete_task(self, task, task_date=date.today()):
        query = "UPDATE todo_list SET completed = %s WHERE task = %s AND date = %s"
        task = task.strip().lower()
        try:
            with self.db.open_database() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (False, task, task_date))
                conn.commit()
                logging.info(f"Task '{task}' marked as incomplete for date {task_date}.")
        except Exception as e:
            logging.error(f"Failed to uncomplete task: {e}")
            raise