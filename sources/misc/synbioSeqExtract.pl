#!/usr/bin/perl

######################################################################
# This is an automatically generated script to run your query.
# To use it you will require the InterMine Perl client libraries.
# These can be installed from CPAN, using your preferred client, eg:
#
#    sudo cpan Webservice::InterMine
#
# For help using these modules, please see these resources:
#
#  * https://metacpan.org/pod/Webservice::InterMine
#       - API reference
#  * https://metacpan.org/pod/Webservice::InterMine::Cookbook
#       - A How-To manual
#  * http://www.intermine.org/wiki/PerlWebServiceAPI
#       - General Usage
#  * http://www.intermine.org/wiki/WebService
#       - Reference documentation for the underlying REST API
#
######################################################################

use strict;
use warnings;

use Data::Dumper;
require LWP::UserAgent;
use JSON;

# Set the output field separator as tab
$, = "\t";
# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');
my $json = JSON->new->allow_nonref;

# This code makes use of the Webservice::InterMine library.
# The following import statement sets SynBioMine Test as your default
# You must also supply your login details here to access this query
use Webservice::InterMine 0.9904 'http://www.flymine.org/synbiomine', 'N1G4u22eA7f8g667V3x3';

# Description: For a given gene (or list of genes) returns the location.

my $template = Webservice::InterMine->template('GeneCoord')
    or die 'Could not find a template called GeneCoord';

# Use an iterator to avoid having all rows in memory at once.
my $it = $template->results_iterator_with(
    # A:  Gene
    opA    => 'IN',
    valueA => 'BanthracisCDC684orthologues_Bsub168_allGenes',
);

# Test cases
#    valueA => 'BsubConstit_NicolasS3',
#    valueA => 'allGenesBsub168',
#    valueA => 'BcereusATCC14579orthologues_Bsub168_allGenes',

print "GeneID\tChrom\tGeneStart..GeneEnd\tStrand\tRegSeqSt..RegSeqEnd\tSeq\n";

while (my $row = <$it>) {
#  print Dumper( $row );

  my $primID = $row->{'primaryIdentifier'};
  my $chromID = $row->{'chromosome.primaryIdentifier'};
  my $start = $row->{'chromosomeLocation.start'};
  my $end = $row->{'chromosomeLocation.end'};
  my $strand = $row->{'chromosomeLocation.strand'};
  my $org = $row->{'organism.shortName'};

  my ($coord1, $coord2) = &getCoord($start, $end, $strand);
#  my $response = &getSeq($coord1, $coord2, $chromID);

  print "$primID\t$chromID\t$start..$end\t$strand\t$coord1..$coord2\t";
    
  my $response = &getSeq($coord1, $coord2, $chromID);
  my $from_json = $json->decode( $response );

#  print Dumper($from_json), "\n";

  foreach my $feature (@{ $from_json->{features} }){
    my $seq = $feature->{seq};
    $seq = ($strand =~ /-/) ? &revComp($seq) : $seq;
#    print $strand, " seq1:$feature->{seq}", " seq2:$seq\n\n";
    print $seq, "\n";
  }

#     print $row->{'primaryIdentifier'}, $row->{'chromosome.primaryIdentifier'},
#         $row->{'chromosomeLocation.start'}, $row->{'chromosomeLocation.end'},
#         $row->{'chromosomeLocation.strand'}, $row->{'organism.shortName'}, "\n";

}

# Selecting 100bp us and 25 bp ds of the translation start
sub getCoord {
  my ($start, $end, $strand) = @_;
  my ($coord1, $coord2);

  if ( $strand =~ /-/ ) {
    $coord2 = $end + 100;
    $coord1 = $end - 25;

  } else {
    $coord1 = $start - 100;
    $coord2 = $start + 25;

  }

  return ($coord1, $coord2);
}

sub getSeq {
  
  my ($start, $end, $chrom) = @_;
  my $base = "http://www.flymine.org/synbiomine/service/sequence?";
#  my $chrom = "NC_000964.3";
#  my $start = "1234";
#  my $end = "1256";
  my $coord = "start=$start\&end=$end";

  my $query = '&query=<query model="genomic" view="Chromosome.sequence.residues"><constraint ' .
  'path="Chromosome" op="LOOKUP" value=' .
  "\"$chrom\"" .
  '/></query>';

  my $url = "$base$coord$query";

  my $agent    = LWP::UserAgent->new;
  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);
  $response->is_success or print "$chrom\tError: " . 
  $response->code . " " . $response->message, "\n";
  return $response->content;

}

sub revComp {

  my $dna = shift;
  my $revcomp = reverse($dna);
  $revcomp =~ tr/ABCDGHMNRSTUVWXYabcdghmnrstuvwxy/TVGHCDKNYSAABWXRtvghcdknysaabwxr/;
  return $revcomp;

}