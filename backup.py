import signal
import argparse
import logging as log
import os
from pathlib import Path
import errno
from alive_progress import alive_bar

from backupdef import BackupDef
from entries import FolderEntry
from diskspacereserver import DiskSpaceReserver
from util import sanitizeFilename


def backup(source: str, destination: str):
    folder = FolderEntry.fromFolder(source)
    folder.name = sanitizeFilename(folder.name)
    new_backupdef = BackupDef(folder)

    # Initialize backup defintions
    backupdef_path = os.path.join(destination, f"{folder.name}.cbdef")
    if Path(backupdef_path).is_file():
        current_backupdef = BackupDef.loadFromFile(backupdef_path)
    else:
        current_backupdef = BackupDef(FolderEntry(folder.name))

    delta_backupdef = BackupDef.delta(new_backupdef, current_backupdef)

    # Initialize disk space reservation
    reserver_path = os.path.join(destination, f"{folder.name}.reserved")
    reserver = DiskSpaceReserver(reserver_path, new_backupdef.fileSize * 3)

    # Copy over files until the disk is filled up
    with alive_bar(delta_backupdef.folder.size,
                   monitor="{count:,} / {total:,} bytes [{percent:.2%}]",
                   stats="({rate:,.0f}b/s, eta: {eta}s)") as bar:
        while delta_backupdef.folder.contents or delta_backupdef.folder.deleted:
            try:
                # Before starting to copy over files, reserve space for the eventual backupdef
                reserver.reserve()

                # Copy the files
                delta_backupdef.processDelta(current_backupdef, source, destination, bar)
            except KeyboardInterrupt:
                # Script was ended by ctrl-c, save backupdef and exit
                reserver.release()
                current_backupdef.saveToFile(backupdef_path)
                print("The copying was interrupted, the progress has been saved.")
                exit()
            except Exception as e:
                if e.errno == errno.ENOSPC:
                    # Disk full, save backupdef of files copied up to this point and ask for new destination
                    with bar.pause():
                        reserver.release()
                        current_backupdef.saveToFile(backupdef_path)
                        dest_input = input(f"\aCartridge full, insert next one and enter new path ({destination}): ")
                        if dest_input != "":
                            destination = dest_input
                            backupdef_path = os.path.join(destination, f"{folder.name}.cbdef")
                            reserver.path = os.path.join(destination, f"{folder.name}.reserved")
                else:
                    # Copying error, save backupdef, print exception message, continue copying next file
                    reserver.release()
                    current_backupdef.saveToFile(backupdef_path)
                    log.warning("The copying was interrupted by an error. "
                                "The progress has been saved, the details are below:")
                    log.warning(e)

    # Save backupdef of (presumably all) files copied up to this point
    reserver.release()
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
