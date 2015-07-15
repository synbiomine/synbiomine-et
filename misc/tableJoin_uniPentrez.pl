#!/usr/bin/perl -w
#
# 
#

use strict;
use warnings;
#use Getopt::Long;

my $usage = "Usage: tablejoiner_col1.pl    file1 file2

Takes two files and executes a join on the first column - if they match.
\n";

unless ( $ARGV[0] ) { die $usage }

### command line options ###
# my (%opts, $join1, $join2, @output);
# 
# GetOptions(\%opts, 'help', 'first=i', 'second=i', 'output=i@');
# defined $opts{"help"} and die $usage;
# 
# defined $opts{"first"} and $join1 = $opts{"first"};
# defined $opts{"second"} and $join2 = $opts{"second"};
# defined $opts{"output"} and @output = @{$opts{"output"}};
# 
# if (@output)
# {
#   for my $testval (0 .. $#output)
#   {
#     die $usage if (($output[$testval] < 1) 
# 		   || ($output[$testval] > 4));
#   }
# }

### script body ###
my $file1 = $ARGV[0]; # eg. diffExpr file
my $file2 = $ARGV[1]; # eg. blast results file

open(FILE1, "< $file1") || die "cannot open $file1: $!\n";
open(FILE2, "< $file2") || die "cannot open $file2: $!\n";

# open(JOIN, "join -1 $join1 -2 $join2 $file1 $file2 |") 
#    or die "Couldn't fork: $!\n";

my (%colF1, %colF2);

while (<FILE1>) 
{
  chomp;
  my ($f1col1, $other) = split(/\t/, $_, 2);
  $colF1{$f1col1} = $other;
}
close FILE1;

while (<FILE2>) 
{
  chomp;
  my ($f2col1, $other) = split(/\t/, $_, 2);
  $colF2{$f2col1} = $other;
}
close FILE2;

foreach my $key ( keys %colF1) {

  if ( exists $colF2{$key} ) {
    print $key, "\t", $colF1{$key}, "\t", $colF2{$key}, "\n";
  } else {
    print $key, "\t", $colF1{$key}, "\tNOT FOUND in BLAST FILE\n";
  }
}


