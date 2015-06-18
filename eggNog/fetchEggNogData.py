#!/usr/bin/python

import argparse
import ftplib
import os.path

#################
### FUNCTIONS ###
#################
def logEyeCatcher(text):
  print "~~~ %s ~~~" % text

def assemblePrereqFiles():
  logEyeCatcher("Checking pre-requisite data files")

  eggNogFtpHost = 'eggnog.embl.de'
  eggNogFtpPath = 'eggNOG/4.0/'

  files = set(['eggnogv4.funccats.txt', 'description/bactNOG.description.txt.gz', 'funccat/bactNOG.funccat.txt.gz', 'members/bactNOG.members.txt.gz', 'id_conversion.tsv'])
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

    ftp = ftplib.FTP(eggNogFtpHost)
    ftp.login()
    ftp.cwd(eggNogFtpPath)

    for f in missingFiles:
      fbn = os.path.basename(f)
      fh = open(fbn, 'w')
      print "Downloading %s" % f
      ftp.retrbinary("RETR %s" % f, fh.write)
      fh.close()

    ftp.close()

############
### MAIN ###
############
parser = argparse.ArgumentParser('Retrieve required EggNOG files and filter required data by organism taxon IDs.')
args = parser.parse_args()

assemblePrereqFiles()
