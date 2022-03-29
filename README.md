# CartridgeBackup
A very basic backup script that can be used to make incremental backups onto multiple, smaller drives(cartridges) from one larger source drive or folder.

This script separately creates and stores an index of all file and folder names that are currently backed up, along with their creation/modification date. When another backup is made this file is checked to ensure only additions, modifications and deletions are copied as part of this later backup.

## Prerequisites
Requires python >3.5

## Usage
### Backup
Run `backup.py` with the source and destination as follows:
```
python backup.py source_path destination_path
```
You can use the `-v` flag for output on the current operations being performed.
Once the current cartridge is full, you will be asked to insert and provide the path to the next one.

If an exception occurs while copying a file, the current progress will be saved, so you can restart the backup and it will just be an incremental backup to the part that didn't fail.

### Restore
To restore, simply start with the first cartridge and copy all the files back. For each next cartridge, copy and when duplicates occur, choose to only keep the most recent files.

Finally, run `restoredeletions.py` with the backup defenition file that is on the last cartridge to delete any files that existed on earlier backups, but were deleted before the last backup was done:
```
python restoredeletions.py name.cbdef restore_destination_path
```
You will first be shown a list of deletions and be asked to confirm them before any files are actually deleted.