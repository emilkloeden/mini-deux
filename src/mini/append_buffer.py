import sys


class AppendBuffer:
    def __init__(self, string: str = ""):
        self.string = string

    def append(self, string: str):
        self.string += string

    def flush(self):
        sys.stdout.write(self.string)
        sys.stdout.flush()
        self.string = ""
