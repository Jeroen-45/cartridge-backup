import os
from pathlib import Path
import logging as log
from enum import Enum
import shutil


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

    def processDelta(self, older_folder_entry: 'FolderEntry', source: str, destination: str):
        """
        Actually copy over the data on disk from source to destination.
        At the same time, move entries from this(the delta) entry to the older folder entry.
        """
        # Transfer deletions
        older_folder_entry.deleted = {**older_folder_entry.deleted, **self.deleted}

        # Determine current path
        current_dest_path = os.path.join(destination, self.name)

        # Create current folder at destination
        log.info(f"Creating folder {current_dest_path}")
        if not os.path.exists(current_dest_path):
            os.makedirs(current_dest_path)

        # Transfer additions/modifications
        for entry in list(self.contents.values()):
            if type(entry) == FolderEntry:
                new_folder_entry = FolderEntry(entry.name)
                older_folder_entry.addFolder(new_folder_entry)

                entry.processDelta(new_folder_entry, os.path.join(source, entry.name), current_dest_path)

                self.contents.pop(entry.name)
            else:
                file_src_path = os.path.join(source, entry.name)

                log.info(f"Copying {file_src_path} to {current_dest_path}")
                shutil.copy2(file_src_path, current_dest_path)

                older_folder_entry.addFile(self.contents.pop(entry.name))

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
