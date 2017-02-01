from lxml import etree

class Model:
    def __init__(self, fn):
        self._modelTree = etree.parse(fn)


class Document:
    def __init__(self, model):
        self._model = model
        self._nextItemNumber = 1
        self._items = []

    def addItem(self, item):
        """
        Add an item to this document.

        Items can be changed after they are added (e.g. additional references added to a collection)
        :param item:
        :return: the item appended
        """

        self._items.append(item)

        return item

    def createItem(self, className):
        """
        Create an item in the given document.
        This factory method should always be used rather than the constructor.
        """

        item = Item(self._model, className)
        item._id = "0_%d" % self._nextItemNumber
        self._nextItemNumber += 1

        return item

    def write(self, outFn):
        """
        Write the document to the filesystem
        """
        with open(outFn, 'w') as f:
            f.write(str(self))

    def __str__(self):
        itemsTag = etree.Element("items")

        for item in self._items:
            itemTag = etree.SubElement(itemsTag, "item",
                                       attrib={"id": item._id, "class": item._className, "implements": ""})

            for name, value in item._attrs.items():
                if isinstance(value, list):
                    collectionTag = etree.SubElement(itemTag, "collection", attrib={"name": name})
                    for referencedItem in value:
                        etree.SubElement(collectionTag, "reference", attrib={"ref_id": referencedItem._id})
                elif isinstance(value, Item):
                    etree.SubElement(itemTag, "reference", attrib={"name": name, "ref_id": value._id})
                else:
                    # print "Writing attribute [%s]:[%s]" % (name, value)
                    etree.SubElement(itemTag, "attribute", attrib={"name": name, "value": str(value)})

        return etree.tostring(itemsTag, pretty_print=True).decode('unicode_escape')


class Item:
    def __init__(self, model, className):
        self._model = model

        # TODO: check this against the model
        self._className = className

        self._attrs = {}

    def addAttribute(self, name, value):
        """
        Add an attribute to this item.
        If the value is empty then nothing is added since InterMine doesn't like this behaviour.
        """

        if value != "":
            self._attrs[name] = value

    def addToAttribute(self, name, value):
        """
        Add a value to an attribute.  If the attribute then has more than one value it becomes a collection.
        An attribute that doesn't already exist becomes a collection with a single value.
        """

        if name in self._attrs:
            self._attrs[name].append(value)
        else:
            self._attrs[name] = [value]

    def getAttribute(self, name):
        return self._attrs[name]

    def hasAttribute(self, name):
        return name in self._attrs

    def getClassName(self):
        return self._className