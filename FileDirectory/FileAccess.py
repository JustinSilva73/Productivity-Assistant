import os
import subprocess
import platform
from fuzzywuzzy import process

file_direct = 'C:/Users/justi/Server'

class FileAccess:
    def __init__(self):
        self.directory = file_direct

    def fuzzy_search(self, filename):
        files = []
        for root, _, filenames in os.walk(self.directory):
            files.extend([os.path.join(root, f) for f in filenames])
        best_match = process.extractOne(filename, files)
        return best_match[0] if best_match else None

    def open_file(self, filename):
        file_path = self.fuzzy_search(filename)
        if not file_path or not os.path.isfile(file_path):
            return f"File {filename} not found in directory {self.directory}."

        try:
            if platform.system() == 'Windows':
                if file_path.endswith('.txt'):
                    subprocess.call(['notepad.exe', file_path])
                else:
                    os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
            return f"File {filename} opened successfully."
        except Exception as e:
            return f"Failed to open file {filename}. Error: {str(e)}"


# Example usage:
# file_access = FileAccess('C:/path/to/your/local/directory')
# print(file_access.list_files())
# print(file_access.open_file('example.docx'))