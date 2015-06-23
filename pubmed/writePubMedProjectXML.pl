#!/usr/bin/perl

use strict;
use warnings;

use Getopt::Std;
use XML::LibXML;

use lib '../modules/perl';
require ImProjectXml;

use feature ':5.12';

my $usage = "Usage:writePubMedProjectXML.pl [-h] [-i <project-xml-path>] <data-path> <info-file-path> <taxon-id-path>

synopsis: read the taxon id file and creates an InterMine project XML <source> entry
If a <project-xml-path> is given then this entry is inserted directly into the given project XML
otherwise it is printed on stdout

options:
\t-h\tthis usage
";

my (%opts, $insert);

getopts('hi:', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"i"} and $insert++;
my $insertPath = $opts{i};

@ARGV > 2 or die $usage;

my ($dataPath, $infoFilePath, $taxonIdPath, $projectXmlPath) = @ARGV;

open TAXONS, $taxonIdPath or die "Could not open $taxonIdPath: $!";
my $taxonIds = <TAXONS>;
chomp($taxonIds);
close TAXONS;

my $sourceXml 
  = ImProjectXml::generateSource(
    "pubmed-gene", "pubmed-gene", 0, 
    [
      ['src.data.dir', 'location', $dataPath], 
      ['pubmed.organisms', $taxonIds],
      ['src.data.dir.includes', "gene2pubmed"],
      ['infoFile', $infoFilePath]
    ]);

if ($insert) {
  ImProjectXml::insertSourceIntoProjectXml($insertPath, $sourceXml);
} else {
  say $sourceXml;
}
