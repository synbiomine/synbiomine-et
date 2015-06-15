#!/usr/bin/perl -w

use strict;
use warnings;
use Getopt::Std;

my $usage = "Usage: parseGEOseries.pl organismID_file analysis_methods_file GEOseries_matrix_file

Options:
-h\tthis help
-l\twhen expression values are already reported as log2 values. 
Default behaviour assumes 'absolute' expression values. 

\n";

### command line options ###
my (%opts, $log_flag);
 
getopts('hl', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"l"} and $log_flag++;

use Statistics::Basic::StdDev;
use Statistics::Basic::Mean;

unless ( $ARGV[2] ) { die $usage }

my ( $id_file, $methods_file, $array_file ) = @ARGV;
#my $array_file = $ARGV[1];

open(ID_FILE, "< $id_file") || die "cannot open $id_file: $!\n";

my %ids;
while (<ID_FILE>) {
  chomp;
  my $idLine = $_;
  my ($id, $gene) = split("\t", $idLine, 2);
  $ids{$id} = $gene;
}

close (ID_FILE);

#foreach my $key ( sort { $a <=> $b } keys %ids ) {
#  print "key: " . $key . " value: " . $ids{$key} . "\n";
#}

open(EXP_FILE, "< $array_file") || die "cannot open $array_file: $!\n";
#open(OUT_FILE, "> $out_file.txt") || die "cannot open $out_file: $!\n";

# define variables for parsing header data
my ($data_h, $title, $geoAcc, $pmid, $summary, $protocol, $organism, $expDesc, $geoIDs);

# define arrays for parsing header/ expression data
my (@expHead, @conditions, @matrix);
while (<EXP_FILE>) {
  chomp;
  my $line = $_;

# Series_title
  if ($line =~ /Series_title/) {
    $line =~ s/\!Series_title\t//;
    $line =~ s/\"//g;
    $title = $line;
    next;
  }

# Series_geo_accession
  if ($line =~ /Series_geo_accession/) {
    $line =~ s/\!Series_geo_accession\t//;
    $line =~ s/\"//g;
    $geoAcc = $line;
    next;
  }

# Series_pubmed_id
  if ($line =~ /Series_pubmed_id/) {
    $line =~ s/\!Series_pubmed_id\t//;
    $line =~ s/\"//g;
    $pmid = $line;
    next;
  }

#   !Sample_organism_ch1

# Series_summary
  if ($line =~ /Series_summary/) {
    $line =~ s/\!Series_summary\t//;
    $line =~ s/\"//g;
    $summary = $line;
    next;
  }
# Series_overall_design
  if ($line =~ /Series_overall_design/) {
    $line =~ s/\!Series_overall_design\t//;
    $line =~ s/\"//g;
    $summary .= " ";
    $summary .= $line;
    next;
  }
#
# Sample_label_protocol_ch1
  if ($line =~ /Sample_label_protocol_ch1/) {
    $line =~ s/\!Sample_label_protocol_ch1\t//;
    $line =~ s/\"//g;
    $line =~ s/\t.+//;
    $protocol .= "$line";
    next;
  }

# Sample_organism_ch1
  if ($line =~ /Sample_organism_ch1/) {
     $line =~ /Sample_organism_ch1\t(.+?)\t/;
     $organism = $1;
     $organism =~ s/\"//g;
     next;
  }

# Sample_scan_protocol
  if ($line =~ /Sample_scan_protocol/) {
    $line =~ s/\!Sample_scan_protocol\t//;
    $line =~ s/\"//g;
    $line =~ s/\t.+//;
    $line =~ s/^/Hybridization and /; # fix for Nicolas data
    $line =~ s/was/were/; # fix for Nicolas data
    $protocol .= " ";
    $protocol .= $line;
    next;
  }

# Sample_data_processing - three lines
  if ($line =~ /Sample_data_processing/) {
    $line =~ s/\!Sample_data_processing\t//;
    $line =~ s/\"//g;
    $line =~ s/\t.+//;
    $protocol .= " ";
    $protocol .= $line;
    next;
  }

# sample_title - experiment short names
  if ($line =~ /Sample_title/) {
    $line =~ s/\"coli_//g; # fix for Jozefczuk truncated orgm in exper names
    $line =~ s/\"//g;
    $data_h = $line;
    next;
  }

# Sample_description - experiment long names
#  if ($line =~ /Sample_description/) {
#    $line =~ s/\"//g;
#    $expDesc = $line;
#    next;
#  }

# # Sample conditions description
  if ($line =~ /Sample_characteristics/) {
#    next unless $line =~ /condition/;
    next if $line =~ /strain\:/;
    next if $line =~ /replicate\:/;
    $line =~ s/\"//g;
    $line =~ s/condition: //g;
    $expDesc = $line;
    next;
  }

  if ($line =~ /ID_REF/) {
    $geoIDs = $line;
    next;
  }

  if ( ($geoIDs) && ( $line !~ /series_matrix_table_end/) ) {
    push(@matrix, $line);
  }
}

close (EXP_FILE);

# parse the analysis methods description file
open(METHOD_FILE, "< $methods_file") || die "cannot open $methods_file: $!\n";

my $analysis_methods;
while (<METHOD_FILE>) {
  chomp;
  my $method_line = $_;
  (undef, $analysis_methods) = split("\t", $method_line);
#  print "//ANAL ", $analysis_methods, "\n";
}

close (METHOD_FILE);

# add a description of the analysis methods

print "//TITLE\t$title\n",
  "//GEO_ACC\t$geoAcc\n",
  "//PMID\t$pmid\n",

  "//SUMMARY\t$summary\n",
  "//ORGANISM\t$organism\n",
  "//PROTOCOL\t$protocol\n",
  "//IM_METHOD\t$analysis_methods\n"; # add a description of the analysis methods

# split expression data into new array
@expHead = split("\t", $data_h);
shift (@expHead); # discard header field

@conditions = split("\t", $expDesc);
shift (@conditions); # discard header field

### Dataset specific tweaks
## Jozefczuk 2010 - E. coli
map { s/heatstress/heat stress/d; $_ } @expHead;
map { s/coldstress/cold stress/d; $_ } @expHead; 
map { s/oxidativestress/oxidative stress/d; $_ } @expHead;
map { s/timepoint(\d+)/timepoint_$1/d; $_ } @expHead;

## Nicolas 2010 data - B. sub
# remove replicate info from the exp descns
# this is the format for Nicolas data but does not seem to be standardised!
map { s/_replicate \d//d; $_ } @conditions; 
map { s/_technical replicate of replicate \d//d; $_ } @conditions;

# Test whether condition details are informative
# That is, have 'spaces' that may be a description
my $spaces = grep /\s/, @conditions;

#print "TEST: ", $conditions[-1], "\n";

# going to be used to track seen items
my (%seen);

my $posn = 0;

# make abbreviated experiment short name header
foreach my $head (@expHead) {
  $head =~ m/(.+)_/; # grab all exper text before _replicate info
  my $exp = $1;

# in Nicolas data, technical rep represented _/t
  if ($exp =~ m"/t") {
    $posn++; # increment array posn
    next; # get rid of technical replicates
  }
  
  $exp =~ s/ /_/;

  push ( @{ $seen{$exp} }, $posn ); # start recording positions of seen elements
#  print "$exp, $rep, $posn\n";
  $posn++; # incr. array posn
}

my %col_order;
foreach my $key (keys %seen) {
  $col_order{$key} = $seen{$key}[-1];
#  print "CHECK: ", $key, "\t", join('; ', @{ $seen{$key} } ), "\n";
}

### Here ###

print "//CONDITIONS"; # print exp conditions leader

# get condition list using our stored position order
for my $key ( sort { $col_order{$a} <=> $col_order{$b} } keys %col_order ) {
  my $posn = $col_order{$key};
  my $exper = $key;
  $exper =~ s/_/ /g;
  
#  print "\nPOSN_CHECK: ", $key, "\t", $conditions[$posn], "\t", join('; ', @{ $seen{$key} } ), "\n"; ## for testing

# Some GEO sets don't provide 
# additional useful info in the descn
# If not, use exp header again
  if ($spaces) {
    print "\t", $conditions[$posn];
  } else {
    print "\t", $exper;
  }
}

print "\n";

print "//EXPERIMENTS"; # print leader for abbrev. exp headers

# exp headers preserving order
for my $key ( sort { $col_order{$a} <=> $col_order{$b} } keys %col_order ) {
  print "\t", $key;
}

print "\n";

print "//HEADER_END\n";

## print "N: ", scalar(@matrix), "\n"; # for testing

# loop through the data matrix
for my $entry (@matrix)
{
  my @exprVal = split("\t", $entry); # extract data columns
  my $name = shift(@exprVal); # first element is identifier
  
  $name =~ s/\"//g;

# provide gene ref based on identifier look-up
  if ( exists $ids{$name} ) {
    print $name, "\t", $ids{$name};
#  print $name;
  }
  else {
    warn "NO IDENTIFIER: $entry\n";
    next;
 }

# process each data set calculating mean, log2 fold change and cv
  my (@newData, @CVs, @rowVals);
  for my $key ( sort { $col_order{$a} <=> $col_order{$b} } keys %col_order ) 
  {
#    print "\nSLICE:", $key, "\t", join('; ', @{ $seen{$key} } ), "\n"; # for testing

# retrieve data slices for each exper + replicates
    my ($currVal, @slice);
    for my $val (@{ $seen{$key} } ) {
      $currVal = $exprVal[$val];
      push(@slice, $currVal);
      push(@rowVals, $currVal);
    }
#    print "$name: ", join("; ", @slice); # for testing

# send data to subroutine for analysis
# returns mean, std dev, coeff of variation and replicate count
    my ($mean, $sd, $cv, $reps) = &computeStats( \@slice );
    $mean = ($mean) ? $mean : $currVal;
    $cv = "" if ($reps < 2);
    push (@newData, $mean);
    push (@CVs, $cv);
#    print "\t$mean, $sd, $cv, $reps\n";

  }

  my ($row_mean, $row_sd, $row_cv, $row_reps) = &computeStats( \@rowVals );

# In GEO some data are given as absolute expr values, 
# some as log2 - we need to standardise by converting
# absolute to log2
  my @diffExpr;
  if ($log_flag) {
    @diffExpr = map { $_ - $row_mean } @newData; # log2 data mean - log2 global mean
  }
  else {
    my $log2_row_mean = log_base2($row_mean); ## log2 fold change if abs vals
    my @log2Data = map { log_base2($_) } @newData; ### 
    @diffExpr = map { $_ - $log2_row_mean } @log2Data;
    @newData = @log2Data; # overwrite abs expr vals with log2 vals
  }
  
# round long numbers to 3 decimal places
  my $round_expr = &stround(3, \@newData);
  my $round_diff = &stround(3, \@diffExpr);
  my $round_cv = &stround(3, \@CVs);
#  print "\t$row_mean, $row_sd, $row_cv, $row_reps\n";

  for (my $i = 0; $i < @diffExpr; $i++) {
    print  "\t", @{ $round_expr }[$i], "|", @{ $round_diff }[$i], "|", @{ $round_cv }[$i];
  }
  print "\n";
}

print "//END_DATA\n";

### subroutines ###
sub computeStats {

  my ($data) = @_;
  my $mean = new Statistics::Basic::Mean($data)->query;
  my $sd = ($mean) ? new Statistics::Basic::StdDev($data)->query : undef;

# For testing calcs
#  my $mean = &average($data);
#  my $sd = ($mean) ? &stdev($data) : "NA";

  my $cv = ($mean) ? (($sd / $mean) * 100) : undef;
#  print "\nCALC:\t$mean, $sd, $cv, ", scalar(@$data), "\n"; # for testing
  return ( $mean, $sd, $cv, scalar(@$data) );
}

# calculate log2 of abs expr values
sub log_base2 {
  my $value = shift;
  my $base = 2;
  
  return unless ($value);

  return log($value)/log($base);
}


## round long numbers to defined length
sub stround {
    my( $places, $arrRef ) = @_;

    my @arrRound;
    foreach my $n ( @{ $arrRef } ) {
      if ($n =~ /\d/) {
	my $sign = ($n < 0) ? '-' : '';
	my $abs = abs $n;
	my $val = $sign . substr( $abs + ( '0.' . '0' x $places . '5' ), 0, $places + length(int($abs)) + 1 );
	push(@arrRound, $val);
      } else {
	my $val = $n;
	push(@arrRound, $val);
      }
    }
    return (\@arrRound);
}

### Test Calcs
### calculate mean by hand to check values
sub average{
        my($data) = @_;
        if (not @$data) {
                die("Empty array\n");
        }
        my $total = 0;
        foreach (@$data) {
                $total += $_;
        }
        my $average = $total / @$data;
        return $average;
}

### calculate stdev by hand to check values
sub stdev{
        my($data) = @_;
        if(@$data == 1){
                return 0;
        }
        my $average = &average($data);
        my $sqtotal = 0;
        foreach(@$data) {
                $sqtotal += ($average-$_) ** 2;
        }
#        my $std = ($sqtotal / (@$data-1)) ** 0.5;
        my $std = ($sqtotal / (@$data)) ** 0.5;
        return $std;
}

### not used
sub uniq {
  my %seen;
  return grep { !$seen{$_}++ } @_;
};
