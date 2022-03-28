import argparse
import logging as log
import os
from pathlib import Path
import errno

from backupdef import BackupDef
from entries import FolderEntry
from util import sanitizeFilename


def backup(source: str, destination: str):
    folder = FolderEntry.fromFolder(source)
    new_backupdef = BackupDef(folder)

    backupdef_path = os.path.join(destination, f"{sanitizeFilename(folder.name)}.cbdef")
    if Path(backupdef_path).is_file():
        current_backupdef = BackupDef.loadFromFile(backupdef_path)
    else:
        current_backupdef = BackupDef(FolderEntry(Path(source).parts[-1]))

    delta_backupdef = BackupDef.delta(new_backupdef, current_backupdef)

    # Copy over files until the disk is filled up
    while delta_backupdef.folder.contents or delta_backupdef.folder.deleted:
        # Before starting to copy over files, store the complete new backupdef to the destination.
        # This is both for fallback and for reserving space for the backupdef
        new_backupdef.saveToFile(backupdef_path)

        # Copy the files
        try:
            delta_backupdef.processDelta(current_backupdef, source, destination)
        except Exception as e:
            if e.errno != errno.ENOSPC:
                raise
            else:
                # Disk full, save backupdef of files copied up to this point and ask for new destination
                current_backupdef.saveToFile(backupdef_path)
                dest_input = input(f"Cartridge full, insert next one and enter new path ({destination}): ")
                if dest_input != "":
                    destination = dest_input

    # Save backupdef of (presumably all) files copied up to this point
    current_backupdef.saveToFile(backupdef_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Perform an incremental backup to"
                                                 "multiple, smaller destination drives(cartridges).")
    parser.add_argument("source", help="The source directory")
    parser.add_argument("destination", help="The destination directory")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    backup(args.source, args.destination)
