# CartridgeBackup
A very basic backup script that can be used to make incremental backups onto multiple, smaller drives(cartridges) from one larger source drive or folder.

This script separately creates and stores an index of all file and folder names that are currently backed up, along with their creation/modification date. When another backup is made this file is checked to ensure only additions, modifications and deletions are copied as part of this later backup.

## Prerequisites
- python >3.5
- alive-progress (`pip install alive-progress`)

## Usage
### Backup
Run `backup.py` with the source and destination as follows:
```
python backup.py source_path destination_path
```
You can use the `-v` flag for output on the current operations being performed.
Once the current cartridge is full, you will be asked to insert and provide the path to the next one.
If you are doing an incremental backup, the process is the same, but you start with the latest cartridge connected and set as the destination. The script will automatically detect the definition file already present on the disk and continue by doing an incremental backup compared to the contents of the current and *all* the previous cartridges.

If an exception occurs while copying a file, the file will be skipped and won't be stored in the backup definition, so a future incremental backup(or a retry after the current one is complete) will try copying it again. Additionally, a warning will be logged when such an exception occurs.

### Restore
To restore, simply start with the first cartridge and copy all the files back. For each next cartridge, copy and when duplicates occur, choose to only keep the most recent files.

Finally, run `restoredeletions.py` with the backup defenition file that is on the last cartridge to delete any files that existed on earlier backups, but were deleted before the last backup was done:
```
python restoredeletions.py name.cbdef restore_destination_path
```
You will first be shown a list of deletions and be asked to confirm them before any files are actually deleted.
