import argparse
import logging as log

from backupdef import BackupDef
from entries import FolderEntry


def backup(source: str, destination: str):
    folder = FolderEntry.fromFolder(source)
    backupdef = BackupDef(folder)
    backupdef.saveToFile()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Perform an incremental backup to"
                                                 "multiple, smaller destination drives(cartridges).")
    parser.add_argument("source", help="The source directory")
    parser.add_argument("destination", help="The destination directory")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    backup(args.source, args.destination)
