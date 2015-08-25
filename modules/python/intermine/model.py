#!/usr/bin/python

from lxml import etree

class Model:
  def __init__(self, fn):
    self.modelTree = etree.parse(fn)

class Document:
  def __init__(self, model, outFn):
    self.model = model
    self.outFn = outFn
    self._items = []

  def addItem(self, item):
    self._items.append(item)

class Item:
  def __init__(self, model):
    self.model = model
    self.attrs = {}

  def addAttribute(self, name, value):
    self.attrs[name] = value
