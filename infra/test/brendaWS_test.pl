#!/usr/bin/perl

use strict;
use warnings;
use SOAP::Lite;

# my $resultString = SOAP::Lite
# -> uri('http://www.brenda-enzymes.org/soap2')
# -> proxy('http://www.brenda-enzymes.org/soap2/brenda_server.php')
# -> getKmValue("ecNumber*1.1.1.1#organism*Escherichia coli#")
# -> result; 
# 
# print $resultString, "\n";

my $resultString = SOAP::Lite 
-> uri('http://www.brenda-enzymes.org/soap2') 
-> proxy('http://www.brenda-enzymes.org/soap2/brenda_server.php')
-> getEcNumbersFromOrganism("organism*Escherichia coli") 
-> result;

my @ECs = split("\!", $resultString);

foreach my $ec (@ECs) {
  my @enzData;

  my $kmRef = \&Km(\$ec);

  if ($kmRef) {
    @enzData = split("\#", $$kmRef);
  }

  print join("\t", @enzData), "\n";
}

#print join("\n", @ECs), "\n";
#print $resultString, "\n";

sub Km {
  my $ecRef = shift;
  my $ecNo = $$ecRef;

  my $nullVal = "No Km Found";

  my $resultString = SOAP::Lite
    -> uri('http://www.brenda-enzymes.org/soap2')
    -> proxy('http://www.brenda-enzymes.org/soap2/brenda_server.php')
    -> getKmValue("ecNumber*$ecNo#organism*Escherichia coli#")
    -> result; 

#print $resultString, "\n";

  if ($resultString) {
    return $resultString;
  } 

# else {
#     return $nullVal;
#   }

}