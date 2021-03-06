#!/usr/bin/perl

use strict;
use warnings;

use Getopt::Std;
use XML::LibXML;

use lib '../modules/perl';
require ImProjectXml;

use feature ':5.12';

my $usage = "Usage:writeKeggPathProjectXML.pl [-h] [-i <project-xml-path>] <kegg-data-path> <taxon-id-path>

read the taxon id file and creates an InterMine project XML <source> entry
<kegg-data-path> is the path relative to the InterMine project.xml file
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

@ARGV > 1 or die $usage;

my ($dataPath, $taxonIdPath, $projectXmlPath) = @ARGV;

open TAXONS, $taxonIdPath or die "Could not open $taxonIdPath: $!";
my $taxonIds = <TAXONS>;
chomp($taxonIds);
close TAXONS;

my $sourceXml 
  = ImProjectXml::generateSource(
    "kegg-pathway", "kegg-pathway", 1, 
    [
      ['src.data.dir', 'location', $dataPath], 
      ['kegg.organisms', $taxonIds]
    ]);

if ($insert) {
  ImProjectXml::insertSourceIntoProjectXml($insertPath, $sourceXml);
} else {
  say $sourceXml;
}
