def addDataSource(doc, name, url):
    """
    Add a DataSource to the given InterMine items XML

    Returns the item.
    """

    dataSourceItem = doc.createItem('DataSource')
    dataSourceItem.addAttribute('name', name)
    dataSourceItem.addAttribute('url', url)
    doc.addItem(dataSourceItem)

    return dataSourceItem

def addDataSet(doc, name, sourceItem):
    """
    Add a DataSet to the given InterMine items XML
    :param doc:
    :param name:
    :param sourceItem:
    :return: the item added
    """

    datasetItem = doc.createItem('DataSet')
    datasetItem.addAttribute('name', name)
    datasetItem.addAttribute('dataSource', sourceItem)
    doc.addItem(datasetItem)

    return datasetItem
