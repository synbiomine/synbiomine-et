from lxml import etree

class Project:
    def __init__(self, fn):
        parser = etree.XMLParser(remove_blank_text=True)
        self._projectTree = etree.parse(fn, parser)

    def addSource(self, source):
        sourcesElement = self._projectTree.xpath('/project/sources')[0]

        sourceElement = etree.SubElement(
            sourcesElement, "source", attrib={ 'name':source.name, 'type':source.type, 'dump':source.dump.__str__() })

        for property in source.properties:
            etree.SubElement(sourceElement, "property", attrib=property)

    def toString(self):
        return etree.tostring(self._projectTree, pretty_print=True)

    def write(self, fileName):
        self._projectTree.write(fileName, pretty_print=True)

class Source:
    def __init__(self, name, type, properties, dump = False):
        self.name = name
        self.type = type
        self.properties = properties
        self.dump = dump