#!/usr/bin/perl

# every perl script should start with these two lines.
use strict;
use warnings;

use InterMine::Item::Document;
use InterMine::Model;

my $usage = "usage: $0 taxon_id model_file data_files

data_files: list of analysed GEO series files of format:
mean expression|log2 fold change|CV
\n";

my ($taxon_id, $model_file, $expr_file) = @ARGV;

unless ( $ARGV[2] ) { die $usage }

my $model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(model => $model);

##### TEST DATA ###
#my $data_source = 'B. sub array expression - Nicholas et al.';
#my $organism = 'B. subtilis';
#my $title = "A fabulous experiment with great results";
#my $description = "Here's some interesting stuff about the experiment";
#my $accession = "ID123";
#my $pmid = "pmid1234";
#my @exper = ("exper1", "exper 2");
#my $data = "BSU00010	10.2|20.2|30.2	40.2|50.2|60.2
#BSU00020	1.2|2.2|3.2	4.2|5.2|";

# my @results = split("\n", $data);

my ($title, $accession, $pmid, $organism, $description, $end_headers);
open(EXPR_FILE, "< $expr_file") || die "cannot open $expr_file: $!\n";

my (@experiments, @conditions, @array_data);

while (<EXPR_FILE>) {
  chomp;
  my $line = $_;

  if ($line =~ /TITLE\t(.+)/) {
    $title = $1;
#    print "TIT: ", $title, "\n";
    next;
  }

  if ($line =~ /GEO_ACC\t(.+)/) {
    $accession = $1;
#    print "GAcc: ", $accession, "\n";
    next;
  }

  if ($line =~ /PMID\t(.+)/) {
    $pmid = $1;
#    print "PMID: ", $pmid, "\n";
    next;
  }

  if ($line =~ /ORGANISM\t(.+)/) {
    $organism = $1;
#    print "ORG: ", $organism, "\n";
    next;
  }

  if ($line =~ /SUMMARY\t(.+)/) {
    $description = $1;
#    print "DESC: ", $description, "\n";
    next;
  }

  if ($line =~ /PROTOCOL\t(.+)/) {
    $description .= "\n" . "$1";
#    print "DESC: ", $description, "\n";
    next;
  }

  if ($line =~ /IM_METHOD\t(.+)/) {
    $description .= "\n" . "$1";
#    print "DESC: ", $description, "\n";
    next;
  }

  if ($line =~ /EXPERIMENTS/) {
    @experiments = split("\t", $line);
    shift(@experiments); # discard 'EXPERIMENTS' tag
    next;
  }

  if ($line =~ /CONDITIONS/) {
    @conditions = split("\t", $line);
    shift(@conditions); # discard 'CONDITIONS' tag
    next;
  }

  if ($line =~ /HEADER_END/) {
    $end_headers++;
    next;
  }

  if ( ($end_headers) && ( $line !~ /END_DATA/) ) {
    push(@array_data, $line);
  }

  if ($line =~ /END_DATA/) {
#    print "$line\tREACHED THE END\n";
    last;
  }
} # end while loop

close (EXPR_FILE);

my $org_item = make_item(
    Organism => (
        taxonId => $taxon_id,
    )
);

my $data_source_item = make_item(
    DataSource => (
        name => $title,
    ),
);

my $data_set_item = make_item(
    DataSet => (
        name => "GEO series data set ($accession) for taxon id: $taxon_id",
	dataSource => $data_source_item,
    ),
);

my $publication_item = make_item(
    Publication => (
        pubMedId => $pmid,
    ),
);

my $experiment_item = make_item(
    MicroArrayExperiment => (
	identifier => $accession,
	name => $title,
	description => $description,
	publication => $publication_item,
    ),
);

my @condObjects;
my $cond_count = 0;
while  ($cond_count <= $#conditions ) {
  my $cond_item = make_item( "ExperimentCondition" );
  $cond_item->set( name => $conditions[$cond_count] );
  $cond_item->set( shortName => $experiments[$cond_count] );
  $cond_item->set( experiment => $experiment_item );
  push (@condObjects, $cond_item);
#  print "RES: $conditions[$cond_count] \n";
  $cond_count++;
}

while ( my $result_line = shift @array_data ) {

  my @results = split("\t", $result_line);
  my $id = shift @results;
  my $symbol = shift @results;
  my $gene = shift @results;

############################################
# Set info for gene and write it out
  my $gene_item = make_item(
      Gene => (
	  primaryIdentifier => "$gene",
      ),
  );

  my @results_items;
  my $i = 0;
  while  ($i <= $#results ) {
#  print "RES: $results[$i] \n";

    my ($mean, $log_fold_change, $cv) = split( /\|/, $results[$i], -1);
#  print "VALS: $mean, $log_fold_change, $cv \n";

    my $cond_item = $condObjects[$i];

    my $result_item = make_item("GEOSeriesResult");
    $result_item->set( meanExpr => $mean);
    $result_item->set( log2FoldChange => $log_fold_change );
    $result_item->set( CV => $cv ) if $cv;
    $result_item->set( condition => $cond_item );
    $result_item->set( gene => $gene_item );
    $result_item->set( dataSet => [$data_set_item] );
    push( @results_items, $result_item);

    push( @{ $condObjects[$i]->{'results'} }, $result_item );

    $i++;
  }

  $gene_item->set( expressionResults => \@results_items );


} # end results loop

# give the experiment a collection of conditions
$experiment_item->set( conditions => \@condObjects );

$doc->close(); # writes the xml
exit(0);

######### helper subroutines:

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);
    if ($item->valid_field('organism')) {
        $item->set(organism => $org_item);
    }
    return $item;
}
