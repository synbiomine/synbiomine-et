#!/usr/bin/perl

use strict;
use warnings;

use Getopt::Std;
use XML::LibXML;

use lib '../modules/perl';
require ImProjectXml;

use feature ':5.12';

my $usage = "Usage:writeUniprotProjectXML.pl [-h] [-i <project-xml-path>] <data-path> <taxon-id-path>

synopsis: read the taxon id file and creates Uniprot InterMine project XML <source> entry
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

my ($dataPath, $taxonIdPath) = @ARGV;

open TAXONS, $taxonIdPath or die "Could not open $taxonIdPath: $!";
my $taxonIds = <TAXONS>;
chomp($taxonIds);
close TAXONS;

{
  my $sourceXml 
    = ImProjectXml::generateSource(
      "uniprot", "uniprot", 1,
      [
        [ 'uniprot.organisms', $taxonIds ],
        [ 'createinterpro', 'true' ],
        [ 'creatego', 'true' ],
        [ 'src.data.dir', 'location', $dataPath ]
      ]);

  if ($insert) {
    ImProjectXml::insertSourceIntoProjectXml($insertPath, $sourceXml);
  } else {
    say $sourceXml;
  }
}

{
  my $sourceXml
    = ImProjectXml::generateSource(
      "uniprot-fasta", "fasta", 0,
      [
        [ 'fasta.taxonId', $taxonIds ],
        [ 'fasta.className', 'org.intermine.model.bio.Protein' ],
        [ 'fasta.classAttribute', 'primaryAccession' ],
        [ 'fasta.dataSetTitle', 'UniProt data set' ],
        [ 'fasta.dataSourceName', 'UniProt' ],
        [ 'src.data.dir', 'location', $dataPath ],
        [ 'fasta.includes', 'uniprot_sprot_varsplic.fasta' ],
        [ 'fasta.sequenceType', 'protein' ],
        [ 'fasta.loaderClassName', 'org.intermine.bio.dataconversion.UniProtFastaLoaderTask' ]
      ]);

  if ($insert) {
    ImProjectXml::insertSourceIntoProjectXml($insertPath, $sourceXml);
  } else {
    say $sourceXml;
  }
}

{
  my $sourceXml
    = ImProjectXml::generateSource(
      "uniprot-keywords", "uniprot-keywords", 1,
      [
        [ 'src.data.dir', 'location', $dataPath ],
        [ 'src.data.dir.includes', 'keywlist.xml' ]
      ]);

  if ($insert) {
    ImProjectXml::insertSourceIntoProjectXml($insertPath, $sourceXml);
  } else {
    say $sourceXml;
  }
}
