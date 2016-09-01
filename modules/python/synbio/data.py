import os.path
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__) + '/..'))
import intermyne.model as imm
import intermyne.utils as imu

class Collection:
    """
    Represents a collection of datasets
    """

    def __init__(self, basePath):
        self.basePath = basePath
        self.genbankPath = '%s/genbank' % self.basePath
        self.selectedAssembliesPath = '%s/synbiomine_selected_assembly_summary_refseq.txt' % self.genbankPath

        self._model = None
        self._taxons = None

    def getSet(self, name):
        """
        Get the dataset in this collection with the given name.
        """

        path = "%s/%s" % (self.basePath, name)

        if not os.path.exists(path):
            os.mkdir(path)

        return Set(self, path)

    def getModel(self):
        """
        Get the InterMine model for this data collection.
        """

        # Lazy load the model so that scripts that don't need it can still run if it isn't present
        if self._model == None:
            self._model = imm.Model('%s/intermine/genomic_model.xml' % self.basePath)

        return self._model

    def getOrganisms(self):
        """
        Get organisms present as first class entities in this dataset
        Returns a dictionary of taxonId:int => name:string
        """

        orgs = {}

        """
        This works for going through actual assembly files but we will use the selected summary list instead
        for dirPath, dirNames, fileNames in os.walk(self.genbankPath):
            for fileName in fileNames:
                if fileName.endswith('_assembly_report.txt'):
                    with open(os.path.join(dirPath, fileName)) as f:
                        for line in f:
                            line = line.strip()
                            # print 'line: [%s]' % line
                            m = re.match('# Organism name:(.*)', line)
                            if m:
                                name = m.group(1).strip()
                            else:
                                m = re.match('# Taxid:(.*)', line)
                                if m:
                                    taxonId = m.group(1).strip()

                    orgs[taxonId] = name
        """

        with open(self.selectedAssembliesPath) as f:
            for line in f:
                line = line.strip()
                print 'line: [%s]' % line
                # assemblyId, bioproject, biosample, wgs_master, refseq_category, taxonId, species_taxonId, organism_name, intraspecific_name, isolate, version_status, assembly_level, release_type, genome_rep, seq_rel_date, asm_name, submitter, gbrs_paired_asm, paired_asm_comp = line.split('\t')
                components = line.split('\t')

                orgs[int(components[5])] = components[7]

        return orgs

    def getTaxons(self):
        """
        Get the string list of taxons
        """

        # Lazy load the taxons so that scripts that don't need them can still run if it isn't present
        if self._taxons == None:
            self._parseTaxons('%s/taxons/taxons.txt' % self.basePath)

        return set(self._taxons)

    def getTaxonsAsString(self):
        """
        Get the taxons as a single ' ' separated string
        """

        return ' '.join(self.getTaxons())

    def _parseTaxons(self, taxonsPath):
        with open(taxonsPath) as f:
            self._taxons = set(f.read().strip().split())

class Set:
    def __init__(self, dc, basePath):
        self._parentCollection = dc
        self._basePath = basePath
        self._rawPath = '%s/raw' % (self._basePath)
        self._loadPath = '%s/load' % (self._basePath)
        self._logsPath = '%s/logs' % (self._basePath)

        if not os.path.exists(self._rawPath):
            os.mkdir(self._rawPath)

        if not os.path.exists(self._loadPath):
            os.mkdir(self._loadPath)

        if not os.path.exists(self._logsPath):
            os.mkdir(self._logsPath)

    def startLogging(self, logName):
        """
        Start logging to the given log name.  This can be a path in which case only the basename will be used.
        """

        logPath = '%s/%s.log' % (self._logsPath, os.path.basename(logName))

        if os.path.exists(logPath):
            os.remove(logPath)

        sys.stdout = imu.Logger(logPath)

    def getCollection(self):
        return self._parentCollection

    def getLoadPath(self):
        return self._loadPath

    def getRawPath(self):
        return self._rawPath
