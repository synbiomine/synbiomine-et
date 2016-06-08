#!/usr/bin/perl

use strict;
use warnings;
use File::Spec::Functions;
use Getopt::Std;
use XML::LibXML;

# allows us to use 'say' instead of print
use feature ':5.12';

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings('uninitialized');

my $usage = "Usage: writeSynbioMineProjectXML.pl [-vh] dataset_directory

synopsis: reads the dataset's genbank directory and writes associated data that's needed for the build.
The -t option will generate a tab-separated genomes summary file (see below)

options:
\t-h\tthis usage
\t-v\tverbose mode - additional output for debugging
\tgenerated XML entries are inserted directly into the given project.xml file and written back out

";

my (%opts, $verbose);

getopts('hv:', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"v"} and $verbose++;
$insert = 1;

@ARGV > 0 or die $usage;

my $base = $ARGV[0];
my $genbankdir = "$base/genbank";
my $insertPath = "$base/intermine/project.xml";

opendir(DIR, $genbankdir) or die "cannot open dir: $!";

my ($projectXml, $sources_e);
my $xmlParser = XML::LibXML->new();

if ($insert) {
  $projectXml = $xmlParser->parse_file($insertPath);

  my @nodes = $projectXml->getDocumentElement()->findnodes("/project/sources");

  not @nodes and die "Could not find node /project/sources in project XML at $projectXml";

  $sources_e = $nodes[0];
}

# read the sub dir listing - name with assembly IDs
while (my $subdir = readdir DIR) {
  my $currAssemblyDir = "$genbankdir/$subdir";

  next if $subdir =~ /^\.|^\.\./; # ignore ./ and ../
  say "SUB: ", $subdir if ($verbose);

  opendir(CURR, $currAssemblyDir) or die "Cannot open $currAssemblyDir: $!";

  # not sure if we need this now - in the old FTP dir, plasmid annotation were present
  my %gffSize; # keep track of which is the biggest file

  my @list = readdir (CURR);

  my @gff = grep( /gff/, @list ); # make a list of the gff files
  my @report = grep( /txt/, @list ); # make a list of the report files

# which is the biggest gff file - this is probably the chrm
  if ( @gff ) {
    foreach my $file (@gff) {
      my $fSize = -s "$currAssemblyDir/$file";
      $file =~ /^(.+)\.gff/;
      my $ncID = $1;
      $gffSize{$ncID} = $fSize;
    }
  }

  my @keys = sort { $gffSize{$b} <=> $gffSize{$a} } keys %gffSize;
  my $largest = $keys[0];
  say $largest if ($verbose);

  my $report = $report[0];
  say $report if ($verbose);

# We use the assembly report file to get the strain to assembly ID mappings
  open REPORT_IN, "$currAssemblyDir/$report" or die "can't open file: $!";

  my ($taxname, $taxID, $orgm);
  while (<REPORT_IN>) {
    chomp;

# Header format is :
# Organism name:  Bacillus anthracis str. Ames
# Taxid:          198094

    if ($_ =~ /Organism name/) {
      $_ =~ /Organism name:\s+(.+)/;
      $taxname = $1;
      $taxname =~ s/\[//;
      $taxname =~ s/\]//;

      $orgm = $taxname;
      $orgm =~ s/ /-/g;
      $orgm =~ s/\.//g;
    }

    if ($_ =~ /Taxid/) {
      $_ =~ /Taxid:\s+(\d+)/;
      $taxID = $1;
      last;
    }
  }

  close (REPORT_IN);

  my $gffFile = "$largest\.gff";

  say "TAX:$taxname, $taxID" if ($verbose);

  my $chrm = "$largest\.fna"; # chromosome fasta

  try_add_source(
    catdir($currAssemblyDir, $gffFile), $taxID, "$orgm-gff", sub { gen_gff("$orgm-gff", $taxID, $taxname, $subdir, $currAssemblyDir, $gffFile); });
  try_add_source(
    catdir($currAssemblyDir, $chrm), $taxID, "$orgm-chromosome-fasta", sub { gen_chrm("$orgm-chromosome-fasta", $taxID, $taxname, $chrm, $currAssemblyDir); });
    
  closedir(CURR);
}

closedir(DIR);

if ($insert) {
  # For some reason, appendWellBalancedChunk() is destroying the indentation level of the </sources> end tag.
  # This is a super bad way to restore it.
  $sources_e->appendTextNode("  ");

  # say "XML [" . $projectXml->toString() . "]";
  
  # This will put the <?xml... declaration at the top of the file where previously there may have been none.
  # Ideally we would retain exact format but this is a pita
  $projectXml->toFile($insertPath); 
}

exit 0;

sub try_add_source {
  my ($sourceFile, $taxID, $sourceName, $genSub) = @_;

  if (-e $sourceFile) {
    say $sourceFile if ($verbose);

    if ($sources_e->findnodes("source[\@name='$sourceName']")) {
      say "Found existing source $taxID => $sourceName.  Skipping.";
    } else {
      my $xml = $genSub->();

      if ($insert) {
        say "Adding source $taxID => $sourceName";
        $sources_e->appendWellBalancedChunk($xml);
      } else {
        print $xml;
      } 
    }
  }
} 

### subs to print the source XML for properties.xml
sub gen_gff {
  my ($sourceName, $taxID, $taxname, $subdir, $gbDir, $gffFile) = @_;

  # This is terribly messy but detecting the correct indent level automatically
  # in the project XML doc is not trivial
  return <<XML;

    <source name="$sourceName" type="synbio-gff">
      <property name="gff3.taxonId" value="$taxID"/>
      <property name="gff3.seqDataSourceName" value="NCBI"/>
      <property name="gff3.dataSourceName" value="NCBI"/>
      <property name="gff3.seqClsName" value="Chromosome"/>
      <property name="gff3.dataSetTitle" value="$taxname genomic features"/>
      <property name="src.data.dir" location="$gbDir/"/>
      <property name="src.data.dir.includes" value="$gffFile"/>
    </source>
XML
}

sub gen_chrm {
  my ($sourceName, $taxID, $taxname, $chrm, $gbDir) = @_;

  return <<XML;

    <source name="$sourceName" type="fasta">
      <property name="fasta.taxonId" value="$taxID"/>
      <property name="fasta.className" value="org.intermine.model.bio.Chromosome"/>
      <property name="fasta.dataSourceName" value="GenBank"/>
      <property name="fasta.dataSetTitle" value="$taxname chromosome, complete genome"/>
      <property name="fasta.includes" value="$chrm"/>
      <property name="fasta.classAttribute" value="primaryIdentifier"/>
      <property name="src.data.dir" location="$gbDir/"/>
      <property name="fasta.loaderClassName" value="org.intermine.bio.dataconversion.NCBIFastaLoaderTask"/>   
    </source>
XML
}