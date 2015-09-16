#!/usr/bin/perl

# requires
# cpan -i Webservice::InterMine

#use strict;
use warnings;

package SynbioGene2Location;

require Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(geneLocation);

# Set the output field separator as tab
$, = "\t";
# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

# This code makes use of the Webservice::InterMine library.
# The following import statement sets SynBioMine as your default
use Webservice::InterMine 0.9904 'http://www.synbiomine.org/synbiomine';

sub geneLocation {

  my ($org_short, $identifier) = @_;
  # Description: For a given gene (or List of Genes) returns gene identifiers
  # and the location co-ordinates.
  my $query = new_query(class => 'Gene');

  # The view specifies the output columns
  $query->add_view(qw/
      primaryIdentifier
      symbol
      chromosome.primaryIdentifier
      chromosomeLocation.start
      chromosomeLocation.end
      chromosomeLocation.strand
      organism.shortName
  /);

  # edit the line below to change the sort order:
  # $query->add_sort_order('primaryIdentifier', 'ASC');

  $query->add_constraint(
      path        => 'Gene',
      op          => 'LOOKUP',
      value       => "$identifier",
      extra_value => "$org_short",
      code        => 'A',
  );

  # Use an iterator to avoid having all rows in memory at once.
  my @gene_lookups;
  my $it = $query->iterator();
  while (my $row = <$it>) {
      push (@gene_lookups, [$row->{'primaryIdentifier'}, 
			    $row->{'symbol'}, 
			    $row->{'chromosome.primaryIdentifier'},
			    $row->{'chromosomeLocation.start'}, 
			    $row->{'chromosomeLocation.end'},
			    $row->{'chromosomeLocation.strand'}, 
			    $row->{'organism.shortName'} ,])
  }

  return (\@gene_lookups);

}
1;

# for my $result (@gene_lookups) {
#   print join("\t", @{ $result }), "\n";
#}
