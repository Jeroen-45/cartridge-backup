import os
from pathlib import Path
import logging as log
from enum import Enum


class EntryType(Enum):
    FOLDER = 1
    FILE = 2


class FileEntry:
    def __init__(self, name: str, time: int):
        self.name = name
        self.time = time

    def __str__(self) -> str:
        return self.name


class FolderEntry:
    def __init__(self, name: str):
        self.name = name
        self.contents = {}
        self.deleted = {}

    def __str__(self) -> str:
        return (f"{self.name}: ("
                f"Contents: {[str(entry) for entry in self.contents.values()]}, "
                f"Deleted: {[str(entry) for entry in self.deleted]})")

    def fromFolder(path_str: str) -> 'FolderEntry':
        """
        Creates a FolderEntry containing the complete structure of
        actual folders and files present under the given path.
        """
        log.info(f"Indexing {path_str}")
        path = Path(path_str)
        new_folder = FolderEntry(path.parts[-1])
        for entry in os.scandir(path_str):
            if entry.is_file():
                file = FileEntry(entry.name, entry.stat().st_mtime)
                new_folder.addFile(file)
            elif entry.is_dir() and entry.name not in ["$RECYCLE.BIN", "System Volume Information"]:
                folder = FolderEntry.fromFolder(entry.path)
                new_folder.addFolder(folder)

        return new_folder

    def delta(self, older_folder_entry: 'FolderEntry'):
        """
        Computes the changes between this and an older FolderEntry.
        Returns a FolderEntry containing only the changes.
        """
        delta_folder_entry = FolderEntry(self.name)

        # Check for new and modified entries
        for entry in self.contents.values():
            if type(entry) == FolderEntry:
                if entry.name not in older_folder_entry.contents:
                    delta_folder_entry.addFolder(entry)
                else:
                    entry_delta = entry.delta(older_folder_entry.contents[entry.name])
                    if entry_delta.contents or entry_delta.deleted:
                        delta_folder_entry.addFolder(entry_delta)
            else:
                if entry.name not in older_folder_entry.contents:
                    delta_folder_entry.addFile(entry)
                elif entry.time > older_folder_entry.contents[entry.name].time:
                    delta_folder_entry.addFile(entry)

        # Check for removed entries
        for entry in older_folder_entry.contents.values():
            if type(entry) == FolderEntry:
                if entry.name not in self.contents:
                    delta_folder_entry.removeFolder(entry.name)
            else:
                if entry.name not in self.contents:
                    delta_folder_entry.removeFile(entry.name)

        return delta_folder_entry

    def addFolder(self, folder: 'FolderEntry'):
        self.contents[folder.name] = folder
        self.deleted.pop(folder.name, None)

    def removeFolder(self, folder_name: str):
        self.contents.pop(folder_name, None)
        self.deleted[folder_name] = EntryType.FOLDER

    def addFile(self, file: FileEntry):
        self.contents[file.name] = file
        self.deleted.pop(file.name, None)

    def removeFile(self, file_name: str):
        self.contents.pop(file_name, None)
        self.deleted[file_name] = EntryType.FILE
