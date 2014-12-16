#!/usr/bin/perl
#
#

#use strict;
use warnings;

package SynbioRegionSearch;

require Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(regionSearch);

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

sub regionSearch {
  my $region = shift;
  $region =~ m/(NC_.+)\:/;
  my $chromosome = $1; 

  ($chromosome) || die "not found: $chromosome$!\n";

  my $org_short = &fetch_organism($chromosome);
  &region_search($region, $org_short);

}
1;

sub fetch_organism {
  use Webservice::InterMine 0.9904 'http://www.synbiomine.org/synbiomine';

  my $chromosome = shift;

  my $chrom_query = new_query(class => 'Chromosome');

  # The view specifies the output columns
  $chrom_query->add_view(qw/
      primaryIdentifier
      organism.shortName
  /);

  $chrom_query->add_constraint(
      path  => 'Chromosome.primaryIdentifier',
      op    => '=',
      value => "$chromosome",
      code  => 'A',
  );

  # Use an iterator to avoid having all rows in memory at once.
  my $org_short;
  my $it = $chrom_query->iterator();

  while (my $row = <$it>) {
    $org_short = $row->{'organism.shortName'};
  }
  return $org_short;
}

sub region_search {

  use Webservice::InterMine 0.9904;

  my ($region, $org_short) = @_;

#  print "INPUT: $region, $org_short\n";

  my $query = Webservice::InterMine->new_query(class => 'Gene')
				   ->select(qw/symbol primaryIdentifier/)
                                   ->where('chromosomeLocation' => {'OVERLAPS' => [$region]});
#  print $query->to_xml, "\n";
  my ($symbol, $identifier, @genes);
  for my $gene ($query->results()) {
    $symbol = ($gene =~ m/symbol: (.+?)\t/) ? $1 : '';
    $identifier = ($gene =~ m/primaryIdentifier: (.+?)$/) ? $1 : '';
    push (@genes, [$symbol, $identifier]);
#    print "S: $symbol\tID: $identifier\n";
  }
  return ($org_short, \@genes);

}
1;
