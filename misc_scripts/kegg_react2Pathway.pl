#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Std;
require LWP::UserAgent;

use feature ':5.12';

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

my $usage = "usage: $0 output_directory_path

Generates tab delimited file of reaction [tab] [pathways collection]
- or vice versa

Default is reaction centric - reaction:has: pathway collection
-p\tpathway centric - pathway:has: reaction collection 
-v\tverbose output

\n";

### command line options ###
my (%opts, $verbose, $pathOpt);

getopts('hvp', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"v"} and $verbose++;
defined $opts{"p"} and $pathOpt++;

unless ( $ARGV[0] ) { die $usage };

my $url;

if ($pathOpt) {
  $url = "http://rest.kegg.jp/link/reaction/pathway";
} else {
  $url = "http://rest.kegg.jp/link/pathway/reaction";
}

my $agent = LWP::UserAgent->new;

my $request  = HTTP::Request->new(GET => $url);
my $response = $agent->request($request);

$response->is_success or say "Error: " . 
$response->code . " " . $response->message;

my $content = $response->content;
#say $content;
&process_kegg($content);

#say "All done - enjoy your results";
exit(1);

sub process_kegg {

  my ($content) = shift;

  my %react2path;

#  my $out_file = $org . "_gene_map.tab";
# #   open (OUT_FILE, ">$out_dir/$out_file") or die $!;
# #   say "Writing to $out_dir/$out_file" if ($verbose);

  open my ($str_fh), '+<', \$content; # process 

  while (<$str_fh>) {
    chomp;
    next if ($_ =~ /map/);
    $_ =~ s/path://;
    $_ =~ s/rn:?//g;

    if ($pathOpt) {
      my ($reaction, $pathway) = split("\t", $_);
      push( @{ $react2path{$reaction} }, $pathway );
      say "line $reaction - $pathway" if ($verbose);
    } else {
      my ($pathway, $reaction) = split("\t", $_);
      push( @{ $react2path{$pathway} },  $reaction);
      say "line $pathway - $reaction" if ($verbose);
    }
  }

  close ($str_fh);

  my @sorted = map  { $_->[0] }
               sort { $a->[1] <=> $b->[1] }
               map  { /[A-Za-z_-]+(\d+)/ and [$_, $1] }
               keys %react2path;

  for my $key (@sorted) {

#  for my $key (sort { $gene2path {$a} <=> $gene2path {$b} } keys %gene2path) {
    say $key, "\t", join(" ",  @{ $react2path{$key} } );
  }

}
