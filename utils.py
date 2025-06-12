import os, sys

class Logger:
    def __init__(self, filename: str, stream=sys.stdout):
        self.terminal = stream
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.log = open(filename, 'a', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass