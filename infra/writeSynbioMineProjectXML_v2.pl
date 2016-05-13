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

my $usage = "Usage: writeSynbioMineProjectXML.pl [-tvgh] dataset_directory

synopsis: reads the dataset's genbank directory and writes associated data that's needed for the build.
Run with the -g option, writes info for the gff_config file. 
The -t option will generate a tab-separated genomes summary file (see below)

options:
\t-h\tthis usage
\t-g\twrite gff_config file 
\t-t\tprint details in tab view
\t\ttaxID\torganism name\tsubdir\tfile prefix
\t-i\tif neither -g or -t are specified then the generated XML entries are inserted directly into the given project.xml file and written back out
\t  \totherwise the XML will be printed
\t-v\tverbose mode - additional output for debugging

";

my (%opts, $tabView, $gffconfig, $insert, $verbose);

getopts('htgvi:', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"t"} and $tabView++; # tab summary - maps assembly vers to org name & tax ID
defined $opts{"g"} and $gffconfig++; # writes gff_config.txt file to run dir
defined $opts{"v"} and $verbose++; # used for debugging
# defined $opts{"i"} and $insert++;
# Currently we are always inserting but an option may come back again not to insert
$insert = 1;

@ARGV > 0 or die $usage;

my $base = $ARGV[0];
my $genbankdir = "$base/genbank";
my $insertPath = "$base/intermine/project.xml";

# if they want the config, open the file for writing (-g option)
if ($gffconfig) {
  open (GFF_CONF_OUT, ">./gff_config.txt") or die "Can't write file: ./gff_config.txt: $!\n";
  say "Writing ./gff_config.txt"; # reminds you that it goes to a file
}

# open the dir they specified
opendir(DIR, $genbankdir) or die "cannot open dir: $!";

# generate headers if a tab summary is needed (-t option)
say "taxID\torganism name\tsubdir\tfile prefix" if ($tabView);
#say GFF_CONF_OUT "taxID: taxname\talt ID\tlocus_tag\tsymbol\tsynonym" if ($gffconfig);

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
  my $gbDir = "$genbankdir/$subdir"; # generate the dir path

  next if $subdir =~ /^\.|^\.\./; # ignore ./ and ../
  say "SUB: ", $subdir if ($verbose); # keep track of sub-dir

  # Ignore paths here that aren't directories
  not -d $gbDir and next;

  opendir(CURR, $gbDir) or die "Cannot open $gbDir: $!";

  # not sure if we need this now - in the old FTP dir, plasmid annotation were present
  my %gffSize; # keep track of which is the biggest file

  my @list = readdir (CURR); # dir listing of the assembly dir

  my @gff = grep( /gff/, @list ); # make a list of the gff files
  my @report = grep( /txt/, @list ); # make a list of the report files

# which is the biggest gff file - this is probably the chrm
  if ( @gff ) {
    foreach my $file (@gff) {
      my $fSize = -s "$gbDir/$file";
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
  open REPORT_IN, "$gbDir/$report" or die "can't open file: $!";

  my ($taxname, $taxID, $orgm);
  while (<REPORT_IN>) {
    chomp; # take off the line endings

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

  close (REPORT_IN); # close the report file

  my $gffFile = "$largest\.gff";

# some of the next section may not be needed as Julie re-wrote the synbio-gff parser
# it not picks up most of these fields by default

  if ($gffconfig) {
    open GFF_IN, "$gbDir/$gffFile" or die "can't open file $gffFile: $!";

    my @gff_line;
    my ($annotation, $db_Xref, $alt_id, $locus_tag, $symbol, $synonym);
    while (<GFF_IN>) {
      chomp;

# GFF header format e.g.
  # Organism name:  Escherichia coli K-12 MG1655
  # Taxid:          511145

# E. coli file
  # ID=gene0;Dbxref=EcoGene:EG11277,GeneID:944742;Name=thrL;gbkey=Gene;gene=thrL;gene_synonym=ECK0001,JW4367;locus_tag=b0001
# B. subtilis line - most of the strains are like this
  # ID=gene0;Dbxref=GeneID:939978;Name=dnaA;gbkey=Gene;gene=dnaA;locus_tag=BSU00010

      if ($_ =~ /ID=gene0\;/) {
	@gff_line = split("\t", $_);
	$annotation = $gff_line[-1];

	($db_Xref = $1) if ($annotation =~ /.+;Dbxref=(.+?),/);
	($alt_id = $1) if ($db_Xref =~ /(.+):/);
	($symbol = $1) if ($annotation =~ /;gene=(.+?)\;/);
	($synonym = $1) if ($annotation =~ /;gene_synonym=(.+)\;/);

	($locus_tag = $1) if ($annotation =~ /.+;locus_tag=(.+)/);
	$locus_tag =~ s/;old_locus_tag=.+$// if ($locus_tag);

	if ($locus_tag) {
	  say GFF_CONF_OUT "$taxID.terms=gene,CDS";
	  say GFF_CONF_OUT "";

# These parts of the gff annotation are now extracted by default
# 	  if ($alt_id) {
# #	    say GFF_CONF_OUT "$taxID.gene.attributes.Dbxref.$alt_id=primaryIdentifier\n",
# #	      "$taxID.gene.attributes.locus_tag=secondaryIdentifier";
# 	  }
# 	  else {
# #	    say GFF_CONF_OUT "$taxID.gene.attributes.locus_tag=primaryIdentifier";
# 	  }
# 	  if ($symbol) {
# #	    say GFF_CONF_OUT "$taxID.gene.attributes.gene=symbol";
# 	  }
# 	  if ($synonym) {
# #	    say GFF_CONF_OUT "$taxID.gene.attributes.gene_synonym=synonym";
# 	  }
#	  say GFF_CONF_OUT "$taxID.CDS.attributes.Name=primaryIdentifier";
#	  say GFF_CONF_OUT "$taxID.exon.attributes.type=scoreType";
#	  say GFF_CONF_OUT "$taxID: $taxname\t$alt_id\t$locus_tag\t$symbol\t$synonym";
	}
	
  # #       ($chrm, undef, undef, undef, undef, 
  # # 	undef, undef, undef, $annotation) = split("\t", $_);
	last;
      }
    }

    close (GFF_IN); # close GFF annotation file
  }

# generates a tab-delimited summary of the genbank directory
# Provides mappings of assembly IDs to their organisms
  if ($tabView) {
    say "$taxID\t$taxname\t$subdir\t$largest";
    next;
  }

  say "TAX:$taxname, $taxID" if ($verbose);

  my $chrm = "$largest\.fna"; # chromosome fasta
#  my $fasta = "$largest\.frn"; # RNA fasta - we don't use this any more

  if (not($tabView or $gffconfig)) {
    try_add_source(
      catdir($gbDir, $gffFile), $taxID, "$orgm-gff", sub { gen_gff("$orgm-gff", $taxID, $taxname, $subdir, $gbDir, $gffFile); });
    try_add_source(
      catdir($gbDir, $chrm), $taxID, "$orgm-chromosome-fasta", sub { gen_chrm("$orgm-chromosome-fasta", $taxID, $taxname, $chrm, $gbDir); });
  }

  # don't use gene fasta any more
  #  if (-e "$gbDir/$fasta") {
  #    say $fasta if ($verbose);
  #    &fasta_print($orgm, $taxID, $taxname, $fasta, $gbDir);
  #  }
    
  closedir(CURR); # close the assembly dir
}

close (GFF_CONF_OUT) if ($gffconfig); # close the config file if using -g

closedir(DIR); # close the genbank dir

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

# We don't integrate this anymore
# sub fasta_print {
#   my ($orgm, $taxID, $taxname, $fasta, $gbDir) = @_;
# 
#   my $fasta_block = <<EOF;
#     <source name="$orgm-gene-fasta" type="fasta">
#       <property name="fasta.taxonId" value="$taxID"/>
#       <property name="fasta.dataSetTitle" value="$taxname fasta data set for genes"/>
#       <property name="fasta.dataSourceName" value="NCBI"/>
#       <property name="fasta.className" value="org.intermine.model.bio.Gene"/>
#       <property name="fasta.classAttribute" value="primaryIdentifier"/>
#       <property name="fasta.includes" value="$fasta"/>
#       <property name="src.data.dir" location="$gbDir/"/>
#     </source>
# EOF
#  say $fasta_block unless ($tabView or $gffconfig);
# }
