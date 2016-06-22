#!/usr/bin/env perl
use strict;
use warnings;

use Getopt::Long;

use feature ':5.12';

my $usage = "writeConfigs.pl

";

### command line options ###
my (%opts, $go, $unip);

GetOptions(\%opts, 'help', 'go', 'unip');
defined $opts{"help"} and die $usage;

defined $opts{"go"} and $go++;
defined $opts{"unip"} and $unip++;

my $in_file = $ARGV[0];
open IN, "$in_file" or die "can't open file: $in_file $!\n";

my @taxon_list;
while (<IN>) {
  chomp $_;

  @taxon_list = split(/ /, $_);

}

if ($go) {
  open (GO_CONF_OUT, ">./go_config.txt") or die "Can't write file: ./go_config.txt: $!\n";
  say "Writing ./go_config.txt";
}

for my $taxon (@taxon_list) {

  &go_conf($taxon) if ($go);
  
}

close (GO_CONF_OUT);

# my @taxon_list = qw|224308 83333 511145|;

# say join("* ", @taxon_list);

sub go_conf {
  my $id = shift;

  say GO_CONF_OUT $id, ".typeAnnotated=protein\n",
    $id, ".identifier=primaryAccession";

  say GO_CONF_OUT "";

}
