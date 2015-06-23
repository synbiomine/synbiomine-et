#!/usr/bin/perl

use strict;
use warnings;

use feature ':5.12';

use XML::LibXML;

package ImProjectXml;
require Exporter;
=pod
our @ISA = qw(Exporter);
our @EXPORT = qw(generateSource insertSourceIntoProjectXml);
=cut

use Exporter qw(import);
our @EXPORT_OK = qw(generateSource insertSourceIntoProjectXml);

=pod
Generate a source XML entry
$properties is an array reference so that we can preserve property ordering
=cut
sub generateSource {
  my ($sourceName, $type, $dump, $properties) = @_;

  my $xml = "\n";
  $xml .= qq[    <source name="$sourceName" type="$type"];
  if ($dump) { $xml .= qq[ dump="true"] }
  $xml .= ">\n";

  foreach my $tuples (@$properties) {
    $xml .= qq[      <property];
    $xml .= " name=\"" . $$tuples[0] . "\"";
    
    # At the moment I'm only using an alternative value attribute name but this could be done for the key name in the future if necessary
    my ($valueName, $valueValue);

    if (@$tuples == 3) {
      $valueName = $$tuples[1];
      $valueValue = $$tuples[2];
    } else {
      $valueName = "value";
      $valueValue = $$tuples[1];
    }
      
    $xml .= qq[ $valueName="$valueValue"];
    $xml .= qq[/>\n];
  }
  $xml .=   qq[    </source>\n];

  return $xml;
}

sub insertSourceIntoProjectXml {
  my ($insertPath, $sourceXml) = @_;

  my $xmlParser = XML::LibXML->new();
  my $projectXml = $xmlParser->parse_file($insertPath);
  my @nodes = $projectXml->getDocumentElement()->findnodes("/project/sources");
  not @nodes and die "Could not find node /project/sources in project XML at $projectXml";
  my $sources_e = $nodes[0];
  
  $sources_e->appendWellBalancedChunk($sourceXml);

  # For some reason, appendWellBalancedChunk() is destroying the indentation level of the </sources> end tag.
  # This is a super bad way to restore it.
  $sources_e->appendTextNode("  ");

  $projectXml->toFile($insertPath);
}
