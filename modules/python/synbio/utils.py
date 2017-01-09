import jargparse
import intermyne.project as imp
from . import data as sbd

def handleSimpleSourceAddProcess(datasetName, sourceNameInProjectXml, sources):
    """
    Handle a simple source add process.  Anything more complicated will need to handle its own arg parsing, etc.

    :param sourceTypeNameInDataset:
    :param sources:
    :param logName:
    :return:
    """

    parser = jargparse.ArgParser('Add %s source entries to InterMine SynBioMine project XML.' % sourceNameInProjectXml)
    parser.add_argument('colPath', help='path to the data collection.')
    parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
    args = parser.parse_args()

    dc = sbd.Collection(args.colPath)
    ds = dc.getSet(datasetName)
    ds.startLogging(__file__)

    imp.addSourcesToProject(dc.getProjectXmlPath(), sources)
