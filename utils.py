import os, sys

class Logger:
    """
    存储输出日志
    """
    def __init__(self, filename: str, stream=sys.stdout):
        self.terminal = stream
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.log = open(filename, 'a', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()        # 添加：刷新终端输出
        self.log.write(message)
        self.log.flush()             # 保持已有：刷新日志文件写入

    def flush(self):
        self.terminal.flush()
        self.log.flush()