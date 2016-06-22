#!/usr/bin/python

import ftplib
import gzip
import os
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/../modules/python')
import intermyne.utils as imu
import synbio.dataset as sbds

#################
### FUNCTIONS ###
#################
def assemblePrereqFiles(localDir, ftpHost, ftpBase, files):
  imu.printSection("Checking pre-requisite data files")

  missingFiles = set()

  # TODO: If need be this can be more sophisticated to check things like file sizes local vs ftp
  for f in files:
    # Although some of our files are not in the base FTP path, we are going to place them all in our base path
    localPath = os.path.join(localDir, os.path.basename(f))
    # We will be decompressing any compressed files
    if localPath.endswith(".gz"):
      localPath = localPath[:-3]

    if os.path.exists(localPath):
      print "Found %s" % localPath
    else:
      missingFiles.add(f)

  if len(missingFiles) > 0:
    print "Downloading required files from %s.  WARNING: One or more of these may be very large files (>4G)" % eggNogFtpHost

    ftp = ftplib.FTP(ftpHost)
    ftp.login()
    ftp.cwd(ftpBase)

    for f in missingFiles:
      localPath = os.path.join(localDir, os.path.basename(f))
      with open(localPath, 'w') as fh:
        print "Downloading %s" % f
        ftp.retrbinary("RETR %s" % f, fh.write)

      # We could probably decompress on the fly but this is not trivial and files are not big
      if localPath.endswith(".gz"):
        print "Decompressing %s" % localPath
        with gzip.open(localPath) as gh:
          uncompressedPath = localPath[:-3]
          with open(uncompressedPath, 'w') as fh:
            fh.writelines(gh)

        os.remove(localPath)

    ftp.close()

def filterIdsMap(idsMapPath, filteredMapPath, taxonIds, verbose=False):
  imu.printSection("Filtering ID mappings")

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
parser = imu.ArgParser('Retrieve required EggNOG files and filter required data by organism taxon IDs.')
parser.add_argument('eggNogFilesPath', help='path to eggNOG files location. This may be an already populated, partially populated or empty directory.')
parser.add_argument('datasetPath', help='path to the dataset.')
parser.add_argument('-v', '--verbose', action="store_true", help="verbose output")
args = parser.parse_args()

logPath = "%s/logs/fetchEggnogData.log"
sys.stdout = imu.Logger(logPath)

ds = sbds.Dataset(args.datasetPath)

eggNogFtpHost = 'eggnog.embl.de'
eggNogFtpBase = 'eggNOG/4.0/'
files = set(['eggnogv4.funccats.txt', 'description/bactNOG.description.txt.gz', 'funccat/bactNOG.funccat.txt.gz', 'members/bactNOG.members.txt.gz', 'id_conversion.tsv'])

assemblePrereqFiles(args.eggNogFilesPath, eggNogFtpHost, eggNogFtpBase, files)
filterIdsMap(os.path.join(args.eggNogFilesPath, 'id_conversion.tsv'), os.path.join(args.eggNogFilesPath, 'id_conversion_taxons.txt'), ds.getTaxons(), args.verbose)
