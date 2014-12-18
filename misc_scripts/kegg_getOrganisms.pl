#!/usr/bin/perl

use strict;
use warnings;
require LWP::UserAgent;

use feature ':5.12';

my $url = "http://rest.kegg.jp/list/organism";

my $agent = LWP::UserAgent->new;

my $request  = HTTP::Request->new(GET => $url);
my $response = $agent->request($request);

$response->is_success or say "Error: " . 
$response->code . " " . $response->message;

my $content = $response->content;
#say $content;

open my ($str_fh), '+<', \$content;

my %organisms;

while (<$str_fh>) {
  chomp;
  next unless ($_ =~ /Prokaryote/);
  my ($k_tax, $k_code, $org_name, $taxon) = split("\t", $_);
  $organisms{$k_code} = $org_name;
}

close ($str_fh);

for my $key (sort { $organisms {$a} cmp $organisms {$b} } keys %organisms) {
  say $key, "\t", $organisms{$key};
}

#say "All done - enjoy your results";
exit(1);
