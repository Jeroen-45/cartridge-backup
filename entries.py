import os
from pathlib import Path
import logging as log
from enum import Enum
import shutil
import stat
import errno


class EntryType(Enum):
    FOLDER = 1
    FILE = 2


class FileEntry:
    def __init__(self, name: str, time: int, size: int):
        self.name = name
        self.time = time
        self.size = size

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

    @property
    def size(self):
        return sum([entry.size for entry in self.contents.values()])

    def fromFolder(path_str: str, bar=None) -> 'FolderEntry':
        """
        Creates a FolderEntry containing the complete structure of
        actual folders and files present under the given path.
        """
        log.info(f"Indexing {path_str}")
        path = Path(path_str)
        new_folder = FolderEntry(path.parts[-1])
        for entry in os.scandir(path_str):
            if entry.is_file(follow_symlinks=False):
                entry_stat = entry.stat()
                file = FileEntry(entry.name, entry_stat.st_mtime, entry_stat.st_size)
                new_folder.addFile(file)
                if bar != None:
                    bar()
            elif entry.is_dir(follow_symlinks=False) and entry.name not in ["$RECYCLE.BIN", "System Volume Information"]:
                folder = FolderEntry.fromFolder(entry.path, bar)
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

    def processDelta(self, older_folder_entry: 'FolderEntry', source: str, destination: str, bar=None):
        """
        Actually copy over the data on disk from source to destination.
        At the same time, move entries from this(the delta) entry to the older folder entry.
        """
        # Transfer deletions
        older_folder_entry.deleted = {**older_folder_entry.deleted, **self.deleted}
        self.deleted = {}

        # Determine current path
        current_dest_path = os.path.join(destination, self.name)

        # Create current folder at destination
        log.info(f"Creating folder {current_dest_path}")
        if not os.path.exists(current_dest_path):
            os.makedirs(current_dest_path)

        # Transfer additions/modifications
        for entry in list(self.contents.values()):
            if type(entry) == FolderEntry:
                if entry.name not in older_folder_entry.contents:
                    older_folder_entry.addFolder(FolderEntry(entry.name))

                entry.processDelta(older_folder_entry.contents[entry.name],
                                   os.path.join(source, entry.name),
                                   current_dest_path, bar)

                self.contents.pop(entry.name)
            else:
                self.contents.pop(entry.name)
                file_src_path = os.path.join(source, entry.name)

                log.info(f"Copying {file_src_path} to {current_dest_path}")
                try:
                    shutil.copy2(file_src_path, current_dest_path)
                except PermissionError:
                    # The file currently present in the backup is probably read-only,
                    # set write permissions and try one more time
                    # (copy2 will put the read-only back when copying the stats)
                    os.chmod(os.path.join(current_dest_path, entry.name), stat.S_IWRITE)
                    shutil.copy2(file_src_path, current_dest_path)
                except Exception as e:
                    if e.errno == errno.ENOSPC:
                        # Disk full, put entry back in delta
                        self.addFile(entry)
                    # Let the exception be handled by the caller
                    raise

                older_folder_entry.addFile(entry)

                # Update loading bar
                if bar != None:
                    bar(entry.size)

    def processDeletions(self, destination: str, dry_run: bool = True):
        """
        Execute all deletions on the destination folder. When dry_run is enabled,
        print the to-be-deleted files and folders instead of actually deleting them.
        """
        log.info(f"Processing deletions in {destination} - {'Dry run' if dry_run else 'Live run'}")

        # Process deletions in this folder
        for name, entry_type in self.deleted.items():
            delete_path = os.path.join(destination, name)
            if entry_type == EntryType.FOLDER:
                if (dry_run):
                    print(f"Delete folder {delete_path}")
                else:
                    log.info(f"Deleting folder {delete_path}")
                    shutil.rmtree(delete_path)
            else:
                if (dry_run):
                    print(f"Delete file   {delete_path}")
                else:
                    log.info(f"Deleting file    {delete_path}")
                    os.remove(delete_path)

        # Recurse into all deeper folders
        for entry in self.contents.values():
            if type(entry) == FolderEntry:
                entry.processDeletions(os.path.join(destination, entry.name), dry_run)

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
