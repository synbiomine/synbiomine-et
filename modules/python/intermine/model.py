#!/usr/bin/python

from lxml import etree

class Model:
  def __init__(self, fn):
    self.modelTree = etree.parse(fn)
