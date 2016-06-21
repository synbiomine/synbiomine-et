import argparse
import project as imp
import sys

class Logger(object):
    def __init__(self, logPath):
        self.terminal = sys.stdout
        self.log = open(logPath, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def fileno(self):
        return self.log.fileno()

class ArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def handleSimpleSourceAddProcess(sourceTypeNameInDataset, sources, logName):
    """
    Handle a simple source add process.  Anything more complicated will need to handle its own arg parsing, etc.

    :param sourceTypeNameInDataset:
    :param sources:
    :param logName:
    :return:
    """

    parser = ArgParser('Add %s source entries to InterMine SynBioMine project XML.' % sourceTypeNameInDataset)
    parser.add_argument('datasetPath', help='path to the dataset location.')
    parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
    args = parser.parse_args()

    datasetPath = args.datasetPath

    logPath = "%s/logs/%s.log" % (datasetPath, logName)
    sys.stdout = Logger(logPath)

    imp.addSourcesToProject("%s/intermine/project.xml" % datasetPath, sources)

def printSection(text):
    print '~~~ %s ~~~' % text