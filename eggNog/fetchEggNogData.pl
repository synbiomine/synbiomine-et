#!/usr/bin/perl

use strict;
use warnings;

use Getopt::Std;

use feature ':5.12';

my $usage = "Retrieve required EggNOG files and filter required data by organism taxon IDs.

options:
\t-h\tthis usage

";

my (%opts);

getopts('h', \%opts);
defined $opts{'h'} and die $usage;

say "Fin";
