#!/usr/bin/python

import argparse
import ftplib
import os.path

#################
### FUNCTIONS ###
#################
def logEyeCatcher(text):
  print "~~~ %s ~~~" % text

def assemblePrereqFiles(ftpHost, ftpBase, files):
  logEyeCatcher("Checking pre-requisite data files")

  missingFiles = set()

  # TODO: If need be this can be more sophisticated to check things like file sizes local vs ftp
  for f in files:
    fbn = os.path.basename(f)
    if os.path.exists(fbn):
      print "Found %s" % fbn
    else:
      missingFiles.add(f)

  if len(missingFiles) > 0:
    print "Downloading required files from %s.  WARNING: One or more of these may be very large files (>4G)" % eggNogFtpHost

    ftp = ftplib.FTP(ftpHost)
    ftp.login()
    ftp.cwd(ftpBase)

    for f in missingFiles:
      fbn = os.path.basename(f)
      with open(fbn, 'w') as fh:
        print "Downloading %s" % f
        ftp.retrbinary("RETR %s" % f, fh.write)

    ftp.close()

def readTaxonIds(taxonsPath):
  logEyeCatcher("Reading taxon IDs")

  taxonIds = set()

  with open(taxonsPath) as f:
    for line in f:
      taxonIds.update(line.split())

  return taxonIds

def filterIdsMap(idsMapPath, filteredMapPath, taxonIds, verbose=False):
  logEyeCatcher("Filtering ID mappings")

  writeCount = 0

  with open(filteredMapPath, 'w') as fmh:
    with open(idsMapPath) as imh:
      for line in imh:
        parts = line.strip().split('\t')
        for id in taxonIds:
          # It looks like BLAST_KEGG_ID is always the 4th column but the source process for this script
          # did not assume this
          if parts[0] == id and "BLAST_KEGG_ID" in parts[1:]:
            if verbose:
              print "Found %s" % line,

            fmh.write(line),
            writeCount += 1

  print "Wrote %s filtered mappings" % writeCount

############
### MAIN ###
############
parser = argparse.ArgumentParser('Retrieve required EggNOG files and filter required data by organism taxon IDs.')
parser.add_argument('taxonIdsPath', help='path to the taxon IDs file')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

eggNogFtpHost = 'eggnog.embl.de'
eggNogFtpBase = 'eggNOG/4.0/'
files = set(['eggnogv4.funccats.txt', 'description/bactNOG.description.txt.gz', 'funccat/bactNOG.funccat.txt.gz', 'members/bactNOG.members.txt.gz', 'id_conversion.tsv'])

assemblePrereqFiles(eggNogFtpHost, eggNogFtpBase, files)
taxonIds = readTaxonIds(args.taxonIdsPath)
# print "taxons [%s]" % (" ".join(taxonIds))
filterIdsMap('id_conversion.tsv', 'id_conversion_taxons.txt', taxonIds, args.verbose)