import argparse
import sys

class Logger(object):
    def __init__(self, logPath):
        self.terminal = sys.stdout
        self.log = open(logPath, 'a')

    def fileno(self):
        return self.log.fileno()

    def flush(self):
        self.log.flush()

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

def printSection(text):
    print('~~~ %s ~~~' % text)
