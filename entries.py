import os
from pathlib import Path


class FileEntry:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class FolderEntry:
    def __init__(self, name: str):
        self.name = name
        self.contents = {}

    def __str__(self):
        return f"{self.name}: {[str(entry) for entry in self.contents.values()]}"

    def fromFolder(path_str: str):
        """
        Creates a FolderEntry containing the complete structure of
        actual folders and files present under the given path.
        """
        print(f"Indexing {path_str}")
        path = Path(path_str)
        new_folder = FolderEntry(path.parts[-1])
        for entry in os.scandir(path_str):
            if entry.is_file():
                file = FileEntry(entry.name)
                new_folder.addFile(file)
            elif entry.is_dir() and entry.name not in ["$RECYCLE.BIN", "System Volume Information"]:
                folder = FolderEntry.fromFolder(entry.path)
                new_folder.addFolder(folder)

        return new_folder

    def addFolder(self, folder: 'FolderEntry'):
        self.contents[folder.name] = folder

    def addFile(self, file: FileEntry):
        self.contents[file.name] = file