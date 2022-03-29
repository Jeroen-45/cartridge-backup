import signal
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
    folder.name = sanitizeFilename(folder.name)
    new_backupdef = BackupDef(folder)

    backupdef_path = os.path.join(destination, f"{folder.name}.cbdef")
    if Path(backupdef_path).is_file():
        current_backupdef = BackupDef.loadFromFile(backupdef_path)
    else:
        current_backupdef = BackupDef(FolderEntry(folder.name))

    delta_backupdef = BackupDef.delta(new_backupdef, current_backupdef)

    # Copy over files until the disk is filled up
    while delta_backupdef.folder.contents or delta_backupdef.folder.deleted:
        # Before starting to copy over files, store the complete new backupdef to the destination.
        # This is both for fallback and for reserving space for the backupdef
        new_backupdef.saveToFile(backupdef_path)

        # Copy the files
        try:
            delta_backupdef.processDelta(current_backupdef, source, destination)
        except KeyboardInterrupt:
            # Script was ended by ctrl-c, save backupdef and exit
            current_backupdef.saveToFile(backupdef_path)
            print("The copying was interrupted, the progress has been saved.")
            exit()
        except Exception as e:
            if e.errno != errno.ENOSPC:
                # Copying error, save backupdef, then re-raise error
                current_backupdef.saveToFile(backupdef_path)
                print("The copying was interrupted by an error. "
                      "The progress has been saved, the details are below:")
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
    signal.signal(signal.SIGINT, signal.default_int_handler)

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

    log.info(f"Running with source {args.source} and destination {args.destination}")

    backup(args.source, args.destination)
