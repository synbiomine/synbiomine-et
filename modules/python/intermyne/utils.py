from colorama import Fore
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

def printError(text):
    print(Fore.RED + 'ERROR: ' + text + Fore.RESET)

def printWarning(text):
    print(Fore.YELLOW + 'WARNING: ' + text + Fore.RESET)