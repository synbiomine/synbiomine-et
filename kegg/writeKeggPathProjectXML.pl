#!/usr/bin/perl

use strict;
use warnings;

use Getopt::Std;
use XML::LibXML;

use lib '../modules/perl';
use ImProjectXml qw(generateSource);

use feature ':5.12';

my $usage = "Usage:writeKeggPathProjectXML.pl [-h] [-i <project-xml-path>] <kegg-data-path> <taxon-id-path>

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

@ARGV > 1 or die $usage;

my ($keggDataPath, $taxonIdPath, $projectXmlPath) = @ARGV;

open TAXONS, $taxonIdPath or die "Could not open $taxonIdPath: $!";
my $taxonIds = <TAXONS>;
chomp($taxonIds);

my $pathwayXml = generateSource("kegg-pathway", $keggDataPath, "kegg.organisms", $taxonIds);

close TAXONS;

if ($insert) {
  my $xmlParser = XML::LibXML->new();
  my $projectXml = $xmlParser->parse_file($insertPath);
  my @nodes = $projectXml->getDocumentElement()->findnodes("/project/sources");
  not @nodes and die "Could not find node /project/sources in project XML at $projectXml";
  my $sources_e = $nodes[0];
  
  say "Inserting kegg-pathway entry into $insertPath";
  $sources_e->appendWellBalancedChunk($pathwayXml);

  # For some reason, appendWellBalancedChunk() is destroying the indentation level of the </sources> end tag.
  # This is a super bad way to restore it.
  $sources_e->appendTextNode("  ");

  $projectXml->toFile($insertPath);
} else {
  say $pathwayXml;
}
