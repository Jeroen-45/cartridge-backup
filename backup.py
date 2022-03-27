import argparse
import logging as log
import os
from pathlib import Path

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
    # print(delta_backupdef)

    new_backupdef.saveToFile(backupdef_path)


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
