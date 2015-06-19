#!/usr/bin/perl

use strict;
use warnings;

package ImProjectXml;
use Exporter qw(import);
our @EXPORT_OK = qw(generateSource);

sub generateSource {
  my ($sourceName, $dataPath, $taxonIdsName, $taxonIds) = @_;

  return <<XML;

    <source name="$sourceName" type="$sourceName" dump="true">
      <property name="src.data.dir" location="$dataPath/"/>
      <property name="$taxonIdsName" value="$taxonIds"/>
    </source>
XML
}
