import argparse
import logging as log
from pathlib import Path

from backupdef import BackupDef


def restoreDeletions(source_cbdef: str, destination: str):
    if Path(source_cbdef).is_file():
        current_backupdef = BackupDef.loadFromFile(source_cbdef)
    else:
        print("CartridgeBackup definition file not found!")
        exit(1)

    # Restore deletions dry run
    print("The following operations will be executed:")
    current_backupdef.folder.processDeletions(destination)
    confirm_input = input("Are you sure? [y/N] ")
    if (confirm_input.lower() == 'y'):
        # Restore deletions live run
        current_backupdef.folder.processDeletions(destination, False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Restore deletions from a CartridgeBackup defintion file.")
    parser.add_argument("source_cbdef", help="The source .cbdef file")
    parser.add_argument("destination", help="The directory to execute the deletions on")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    restoreDeletions(args.source_cbdef, args.destination)
