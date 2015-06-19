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

sub generateSource {
  my ($sourceName, $dataPath, $taxonIdsName, $taxonIds) = @_;

  return <<XML;

    <source name="$sourceName" type="$sourceName" dump="true">
      <property name="src.data.dir" location="$dataPath/"/>
      <property name="$taxonIdsName" value="$taxonIds"/>
    </source>
XML
}

sub insertSourceIntoProjectXml {
  my ($insertPath, $sourceXml) = @_;

  my $xmlParser = XML::LibXML->new();
  my $projectXml = $xmlParser->parse_file($insertPath);
  my @nodes = $projectXml->getDocumentElement()->findnodes("/project/sources");
  not @nodes and die "Could not find node /project/sources in project XML at $projectXml";
  my $sources_e = $nodes[0];
  
  say "Inserting kegg-pathway entry into $insertPath";
  $sources_e->appendWellBalancedChunk($sourceXml);

  # For some reason, appendWellBalancedChunk() is destroying the indentation level of the </sources> end tag.
  # This is a super bad way to restore it.
  $sources_e->appendTextNode("  ");

  $projectXml->toFile($insertPath);
}
