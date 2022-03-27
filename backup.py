import argparse
from backupdef import BackupDef

from entries import *


def backup(source: str, destination: str):
    folder = FolderEntry.fromFolder(source)
    backupdef = BackupDef(folder)
    backupdef.saveToFile()
    # print(folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Perform an incremental backup to ' +
                                                 'multiple, smaller destination drives(cartridges).')
    parser.add_argument("source", help="The source directory")
    parser.add_argument("destination", help="The destination directory")
    args = parser.parse_args()
    backup(args.source, args.destination)
