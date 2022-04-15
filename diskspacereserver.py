import os


# Reserves disk space by saving binary zeros to a file a given size
class DiskSpaceReserver:
    def __init__(self, path: str, size: int):
        self.path = path
        self.size = size

    def reserve(self):
        with open(self.path, 'wb') as f:
            f.write(b'\0' * self.size)

    def release(self):
        try:
            os.remove(self.path)
        except OSError:
            pass
