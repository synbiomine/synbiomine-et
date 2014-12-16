#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Std;
require LWP::UserAgent;

use feature ':5.12';

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

=head1 NAME

kegg_org_pathway.pl - Service for retrieving organism-specific gene to pathway mappings 
from the KEGG PATHWAY database using the KEGG's web service

=head1 SYNOPSIS

  usage: kegg_org_pathway [-v|-h] file_of_organism_codes [optional: output_directory_path]

  options: 
    -v (verbose) : helpful messaging for debug purposes
    -h (help)    : shows usage

  input: file_of_organism_codes (plain text - one code per line): 

      KEGG organism_codes: 3-4 letter organism codes used by KEGG e.g. 
      eco
      bsu
      hsa

  [optional: output dir    If not specified, defaults to current dir]

  output: writes a file of gene to pathway mappings for each organism
  specified in the input file. Filename is [code]_gene_map.tab.
  File format is:
    gene_id\tpathway1, p2, p3 etc.

  B<NOTE:> KEGG imposes restrictions on download and use by non-academic groups: 
    I<KEGG API is provided for academic use by academic users belonging to>
    I<academic institutions. This service should not be used for bulk data downloads.> 

    For more information, see: http://www.kegg.jp/kegg/rest/

=head1 AUTHOR

Mike Lyne C<< <dev@intermine.org> >>

=head1 BUGS

Please report any bugs or feature requests to C<dev@intermine.org>.

=head1 SUPPORT

You can find documentation for this script with the perldoc command.

    perldoc kegg_org_pathway.pl

=head1 COPYRIGHT AND LICENSE

Copyright 2006 - 2014 FlyMine, all rights reserved.

This program is free software; you can redistribute it and/or modify it
under the same terms as Perl itself.

=head1 FUNCTIONS

=cut

my $usage = "usage: $0 file_of_organism_codes output_directory_path

organism_codes:\t3-4 letter organism codes used by KEGG
e.g.
  eco
  bsu
  hsa

-v\tverbose output

\n";

### command line options ###
my (%opts, $verbose);

getopts('hv', \%opts);
defined $opts{"h"} and die $usage; # help
defined $opts{"v"} and $verbose++; # debugging mode

unless ( $ARGV[0] ) { die $usage }; # check for input file

my ($org_file, $out_dir) = @ARGV;
$out_dir = ($out_dir) ? $out_dir : "\."; # set output dir - or use current by default

open(ORG_FILE, "< $org_file") || die "cannot open $org_file: $!\n"; # open kegg org file

say "Executing KEGG pathways script" if ($verbose);

# process the organism file
while (<ORG_FILE>) {
  chomp; # new lines off
  my $org = $_;
  say "Processing organism: $org" if ($verbose);

  my $content = &kegg_ws($org); # query KEGG WS sub routine with org ID
  sleep(3); # be nice and sleep between requests
  &process_kegg($org, $out_dir, $content); # process the results

}

say "All done - enjoy your results" if ($verbose);
exit(1);

## sub routines ##
# get pathways per organism
sub kegg_ws {

  my $org = shift; # we've been sent the org code
  my $base = "http://rest.kegg.jp/link/pathway/"; # base URL
  my $url = "$base$org"; # org code that was passed

  my $agent = LWP::UserAgent->new; # new agent

# compose request
  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);

# check for positive response or give error message
  $response->is_success or say "$org - Error: " . 
  $response->code . " " . $response->message;

  return $response->content; # return content

}

### process the pathways per organism and write to file in specified dir
sub process_kegg {

# input is org code, output directory and the results from the pathways WS query
  my ($org, $out_dir, $content) = @_; 

  my %gene2path; # instantiate hash for gene to pathway mappings

  my $out_file = $org . "_gene_map.tab"; # specify output file [orgCode]_gene_map.tab
  open (OUT_FILE, ">$out_dir/$out_file") or die $!; # open file for writing
  say "Writing to $out_dir/$out_file" if ($verbose);

  open my ($str_fh), '+<', \$content; # open results as file handle

# loop through org pathway lines 
  while (<$str_fh>) {
    chomp;
    $_ =~ s/path:$org//; # get rid of prefixes
    $_ =~ s/$org://;
    my ($gene, $path) = split("\t", $_); # split the line
    push( @{ $gene2path{$gene} }, $path ); # append pathways to array with gene ID as key
    say "line $gene - $path" if ($verbose);
  }

  close ($str_fh); # close the results fh

# schwartzian transform to sort hash map more efficiently
  my @sorted = map  { $_->[0] }
               sort { $a->[1] <=> $b->[1] }
               map  { /[A-Za-z_-]+(\d+)/ and [$_, $1] }
               keys %gene2path;

# loop through sorted keys and write to out file
  for my $key (@sorted) {
    say OUT_FILE $key, "\t", join(" ",  @{ $gene2path{$key} } );
  }
  say "Finished $org\n" if ($verbose);
  close (OUT_FILE); # clean up

}

__END__
