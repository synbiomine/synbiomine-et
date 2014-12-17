#!/usr/bin/perl
#
#

#use strict;
use warnings;

package SynbioFetchExpression;

require Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(expressionResults);

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

sub expressionResults {

  use Webservice::InterMine 1.0405 'http://met1:8080/synbiomine-exper';

  my ($gene, $org_short) = @_;

  my $query = new_query(class => 'Gene');

  # The view specifies the output columns
  $query->add_view(qw/
      primaryIdentifier
      expressionResults.condition.name
      expressionResults.log2FoldChange
      expressionResults.meanExpr
      expressionResults.CV
      chromosome.primaryIdentifier
      chromosomeLocation.start
      chromosomeLocation.end
      chromosomeLocation.strand
      organism.shortName
      organism.taxonId
      expressionResults.dataSet.name
  /);

  $query->add_constraint(
      path        => 'Gene',
      op          => 'LOOKUP',
      value       => "$gene",
      extra_value => "$org_short",
      code        => 'A',
  );

  # Use an iterator to avoid having all rows in memory at once.
  my $it2 = $query->iterator();
  my @results;
  while (my $row = <$it2>) {
    push (@results, [$row->{'primaryIdentifier'}, 
		      $row->{'expressionResults.condition.name'},
		      $row->{'expressionResults.log2FoldChange'}, 
		      $row->{'expressionResults.meanExpr'},
		      $row->{'expressionResults.CV'}, 
		      $row->{'chromosome.primaryIdentifier'},
		      $row->{'chromosomeLocation.start'},
		      $row->{'chromosomeLocation.end'},
		      $row->{'chromosomeLocation.strand'}, 
		      $row->{'organism.shortName'},
		      $row->{'organism.taxonId'}, 
		      $row->{'expressionResults.dataSet.name'},])

  }
    return ($gene, \@results);
}

1;