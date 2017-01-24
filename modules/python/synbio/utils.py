import jargparse
import jinja2
import yaml

import intermyne.project as imp
from . import data as sbd


def addSourcesToProject(dataCollection, sources):
    """
    This calls through to intermyne.project.addSourcesToProject() but will also do jinja2 template placeholder
    substitution.  The values for this are loaded from config.yaml
    :param dataCollection:
    :param sources: list of intermyne.project.Source
    :return:
    """

    # Copy the config file into the dataset itself and get it from there
    with open('config/config.yaml') as f:
        config = yaml.load(f)

    for s in sources:
        # print('Processing source %s' % s.name)
        for p in s.properties:
            for k, v in p.items():
                # print('Processing %s:%s' % (k, v))
                t = jinja2.Template(v)
                p[k] = t.render(config)

    imp.addSourcesToProject(dataCollection.getProjectXmlPath(), sources)


def handleSimpleSourceAddProcess(datasetName, sources):
    """
    Handle a simple source add process.  Anything more complicated will need to handle its own arg parsing, etc.

    :param datasetName: This must match the directory name in the data collection
    :param sources: list of intermyne.project.Source
    :return:
    """

    parser = jargparse.ArgParser('Add %s source entries to InterMine SynBioMine project XML.' % datasetName)
    parser.add_argument('colPath', help='path to the data collection.')
    parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
    args = parser.parse_args()

    dc = sbd.Collection(args.colPath)
    ds = dc.getSet(datasetName)
    ds.startLogging(__file__)

    addSourcesToProject(dc, sources)
