#!/usr/bin/python

from lxml import etree

class Model:
  def __init__(self, fn):
    self._modelTree = etree.parse(fn)

class Document:
  def __init__(self, model):
    self._model = model
    self._items = []

  def addItem(self, item):
    self._items.append(item)

  def write(self, outFn):
    i = 1
    itemsTag = etree.Element("items")   
    
    for item in self._items:
      itemTag = etree.SubElement(itemsTag, "item", attrib = { "id" : "0_%d" % (i), "class" : item._className, "implements" : "" })
      i += 1

    tree = etree.ElementTree(itemsTag)
    tree.write(outFn, pretty_print=True)

class Item:
  def __init__(self, model, className):
    self._model = model

    # TODO: check this against the model
    self._className = className

    self._attrs = {}

  def addAttribute(self, name, value):
    self._attrs[name] = value
