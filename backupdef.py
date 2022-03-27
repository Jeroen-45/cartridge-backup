import pickle

from entries import FolderEntry


class BackupDef:
    def __init__(self, folder: FolderEntry):
        self.folder = folder

    def __str__(self) -> str:
        return str(self.folder)

    def saveToFile(self, path: str):
        with open(path, 'wb') as pkl_file:
            pickle.dump(self, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)

    def loadFromFile(path: str = None) -> 'BackupDef':
        with open(path, 'rb') as pkl_file:
            return pickle.load(pkl_file)

    def delta(self, older_def: 'BackupDef'):
        """
        Computes the changes between this and an older BackupDef.
        Returns a BackupDef containing only the changes.
        """
        return BackupDef(self.folder.delta(older_def.folder))
