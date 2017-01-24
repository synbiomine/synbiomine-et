import jargparse
import jinja2
import yaml

import intermyne.project as imp
from . import data as sbd

def handleSimpleSourceAddProcess(datasetName, sources):
    """
    Handle a simple source add process.  Anything more complicated will need to handle its own arg parsing, etc.
    The property values can include jinja2 template syntax, where placeholders will be replaced with entries in
    config.yaml

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

    # Copy the config file into the dataset itself and get it from there
    with open('config/config.yaml') as f:
        config = yaml.load(f)

    for s in sources:
        for p in s.properties:
            for k, v in p.items():
                t = jinja2.Template(v)
                p[k] = t.render(config)

    imp.addSourcesToProject(dc.getProjectXmlPath(), sources)
