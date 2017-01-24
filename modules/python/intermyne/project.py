import shutil
from lxml import etree

def addSourcesToProject(projectPath, sources):
    """
    Add sources to a project and write out the project XML, first backing up the existing project XML to <projectPath>.bak

    :param projectPath:
    :param sources:
    :return:
    """

    project = Project(projectPath)

    for source in sources:
        project.addSource(source)

    shutil.copy(projectPath, "%s.bak" % projectPath)
    project.write(projectPath)

class Project:
    def __init__(self, fn):
        parser = etree.XMLParser(remove_blank_text=True)
        self._projectTree = etree.parse(fn, parser)

    def addSource(self, source):
        sourcesElement = self._projectTree.xpath('/project/sources')[0]

        sourceElement = etree.SubElement(
            sourcesElement, "source", attrib={ 'name':source.name, 'type':source.type, 'dump':source.dump.__str__().lower() })

        for property in source.properties:
            etree.SubElement(sourceElement, "property", attrib=property)

    def toString(self):
        return etree.tostring(self._projectTree, pretty_print=True)

    def write(self, fileName):
        self._projectTree.write(fileName, pretty_print=True)

class Source:
    def __init__(self, name, type, properties, dump = False):
        """
        :param name:
        :param type:
        :param properties: An array of dictionaries containing property attributes, e.g. [{'name':'src.data.dir', 'location':'data/ecocyc'}]
        :param dump:
        """
        self.name = name
        self.type = type
        self.properties = properties
        self.dump = dump