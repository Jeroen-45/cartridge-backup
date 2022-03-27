import pickle

from entries import *
from util import sanitize_filename


class BackupDef:
    def __init__(self, folder: FolderEntry, cartridgenum: int = 0):
        self.folder = folder
        self.cartridgenum = cartridgenum

    def saveToFile(self, path: str = None):
        if path is None:
            path = f"{sanitize_filename(self.folder.name)}.cbdef"

        with open(path, 'wb') as pkl_file:
            pickle.dump(self, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
