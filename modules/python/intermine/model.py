#!/usr/bin/python

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
    self._items.append(item)

  """
  Create an item in the given document.
  This factory method should always be used rather than the constructor.
  """
  def createItem(self, className):
    item = Item(self._model, className)
    item._id = "0_%d" % self._nextItemNumber
    self._nextItemNumber += 1

    return item

  """
  Write the document to the filesystem
  """
  def write(self, outFn):
    itemsTag = etree.Element("items")   
    
    for item in self._items:
      itemTag = etree.SubElement(itemsTag, "item", attrib = { "id" : item._id, "class" : item._className, "implements" : "" })

      for name, value in item._attrs.iteritems():
        if isinstance(value, list):
          collectionTag = etree.SubElement(itemTag, "collection", attrib = { "name" : name })
          for referencedItem in value:
            etree.SubElement(collectionTag, "reference", attrib = { "ref_id" : referencedItem._id })
        elif isinstance(value, Item):
          etree.SubElement(itemTag, "reference", attrib = { "name" : name, "ref_id" : value._id })
        else:
          etree.SubElement(itemTag, "attribute", attrib = { "name" : name, "value" : value })

    tree = etree.ElementTree(itemsTag)
    tree.write(outFn, pretty_print=True)

class Item:
  def __init__(self, model, className):
    self._model = model

    # TODO: check this against the model
    self._className = className

    self._attrs = {}

  """
  Add an attribute to this item.
  """
  def addAttribute(self, name, value):
    self._attrs[name] = value

  """
  Add a value to an attribute.  If the attribute then has more than one value it becomes a collection.
  An attribute that doesn't already exist becomes a collection with a single value.
  """
  def addToAttribute(self, name, value):
    if name in self._attrs:
      self._attrs[name].append(value)
    else:
      self._attrs[name] = [ value ]
