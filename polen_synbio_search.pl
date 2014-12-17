#!/usr/bin/perl
#
#

use strict;
use warnings;
use feature ':5.12'; # let's us 'say' instead of 'print'
use JSON;

require LWP::UserAgent;
use Getopt::Std;

# Tell @INC where to find the modules
use lib "/SAN_synbiomine/data/SYNBIO_data/user_perl_modules";

# Load the modules
use SynbioRegionSearch qw/regionSearch/;
use SynbioFetchExpression qw/expressionResults/;

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

my $usage = "Usage: polenBlast.pl options [-p|-s]

Polls the Polen client for new messages. If they're sequence objects, the sequence
is Blasted against the genome to get the location and gene info. Using geneID, the
script queries SynBioMine to retrieve any gene expression data for the gene.

Currently, three different groups use Polen:
\tCambridge : receive messages and itegrate content into SynBioMine, then publish URL
\tUCL : publish links to part characterisation data
\tNewcastle : receive part characterisation messages and publish messages on new models

Output: Constructs a JSON message containing the part data. However,
in future this should probably just provide a perma URL to the integrated object page
in SynBioMine.

Options:
-h\tthis help
-p(art)\tthe polen client should poll for a virtual part
-s(heet\tthe polen client should poll for a data sheet

-d(ebug)\tdebug mode - verbose

Hard-coded Polen client jars are located:
/SAN_synbiomine/data/SYNBIO_data/BLAST/EcoliMG1655
\n";

### command line options ###
my (%opts, $part_flag, $dsheet_flag, $debug);
 
getopts('hpsd', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"p"} and $part_flag++;
defined $opts{"s"} and $dsheet_flag++;
defined $opts{"d"} and $debug++;

unless ( $part_flag | $dsheet_flag ) { die $usage }
#unless ( $part_flag | $dsheet_flag ) { die $usage }

# Set working directory
my $work_dir = "/SAN_synbiomine/data/SYNBIO_data/BLAST/MICROBES";

# Get POLEN datasheet message
# my $test = "21"; # used for testing the dsid retrieval
print "Polling for messages...\n" if $debug; ###
my $message;
$message = `java -jar $work_dir/../EcoliMG1655/polenClient.jar` if $dsheet_flag; # Datasheet message
$message = `java -jar $work_dir/../EcoliMG1655/polenClient_PartSeq.jar` if $part_flag; # Part message

# Who does the message come from?
# Newcastle will publish part sequence
# SynBis will have a data sheet
my ($part_name, $part_sequence);

if ($part_flag) {
#  print "Virtual Part message received containing:\n$message"; ###

  if ($message =~ m/sequence=/) {
    print "Checking virtual parts\n" if $debug;
    ($part_name, $part_sequence) = &part_newcastle($message);
  } 
    else { die "No sequence found in $message\n" }
}

if ($dsheet_flag) {
  print "Datasheet message received containing:\n$message" if $debug; ###
  ($part_name, $part_sequence) = &datasheet_synbis($message);
} 
print $message, "\n" if $debug;

### TEST DATA ###
#my $query = ">EG10061\natgcagaccccgcacattcttatcgttgaagacgagttggtaacacg"; # test seq
#my $query = ">EG10061\natgctgcggggcattcaaaattgaagaaaaggtaacacg"; # test fail seq
# my $query = ">panB\nTTGCCCCCACCAATGTGACTGATAAAATGCCAGACA
# >mdoG\nTTGTCGGAATGGCTGGTTATCCATTAAAATAGATCGGA
# >gloA\nTTGTAATCCAACATTGCGAGCGGCGTAAAGCCGCCGCTATACTAAAACAAC
# >nlpD\nTTCAGTAGGGTGCCTTGCACGGTAATTATGTCACTGG
# >bcp\nTGTACAGAACTCAATGCACAAGGCAGTATTAACGTCGT
# >gcvR\nTTGTATGCATGTTTTTTTTATGCTTTCCTTAAGAACA";


## BLAST sequence against genome
my $query =">$part_name\n$part_sequence";

# write query to a tmp file
open TMP_FILE, ">$work_dir/tmp_file.txt" or die $!; 
print TMP_FILE $query; 
close TMP_FILE;

# set BLAST params
print "BLASTing sequence: $part_sequence\n" if $debug;
my $blast_db = "$work_dir/prokaryote_genomes";
my $blast_out = `blastn -query $work_dir/tmp_file.txt -db $blast_db -evalue 1e-1 -dust no -outfmt 6`;

print "B: ", $blast_out, "\n" if $debug; ###

my @blast_res;
if ($blast_out =~ m/\n/) {
  @blast_res = split("\n", $blast_out);
} else {
  push(@blast_res, $blast_out);
}
print join("\n", @blast_res), "\n" if $debug;

# BLAST output 
# Field	 	Description
# 1	 	Query label.
# 2	 	Target (database sequence or cluster centroid) label.
# 3	 	Percent identity.
# 4	 	Alignment length.
# 5	 	Number of mismatches.
# 6	 	Number of gap opens.
# 7	 	1-based position of start in query. For translated searches (nucleotide queries, protein targets), query start<end for +ve frame and start>end for -ve frame.
# 8	 	1-based position of end in query.
# 9	 	1-based position of start in target. For untranslated nucleotide searches, target start<end for plus strand, start>end for minus strand.
# 10	 	1-based position of end in target.
# 11	 	E-value calculated using Karlin-Altschul statistics.
# 12	 	Bit score calculated using Karlin-Altschul statistics.

#my $region;
for my $result (@blast_res) {
  my ($q_name, $targ, $perc, $a_len, $mism, $gap, 
      + $q_start, $q_end, $db_start, $db_end, $other) = split("\t", $result);

# Test to see if we have results
  unless ($other) { 
    warn "No BLAST hits for QUERY: $part_name $part_sequence\n";
  }

# grab host chromosome info ready for synbiomine query
  my $chromosome;
  if ($targ =~ /\|(NC_.+)\|/) {
    $chromosome = $1;
  } else {
    warn "No Chromosome found for $targ\n";
    next;
  }

# query region co-ordinates
  my ($organism_start, $organism_end, $organism_strand);

  if ($db_start < $db_end) {
    $organism_start = $db_start;
    $organism_end = $db_end;
    $organism_strand = "1";
  } else {
    $organism_start = $db_end;
    $organism_end = $db_start;
    $organism_strand = "-1";
  }

  my $region = "$chromosome:$organism_start..$organism_end";

  my ($gene_from_synbio, $expressionRef, @synbio_expr_results); 
  if ($perc > 99) {
    print "MATCH: BLAST found sequence with: ", $perc, "\% match\n", ###
	  "$part_name, $part_sequence\t$region $organism_strand\n" if $debug;
    print "Searching for genes in $region\n" if $debug;

    my ($org_short, $genesFromSynbio_Ref) = regionSearch($region);  # calls a module to query synbiomine for gene id

    unless ($genesFromSynbio_Ref) { # finish if we didn't find a gene
      print "Sorry. No gene found at $region in SynBioMine\n";
      next ;
    }

    my @synbio_genes = @{$genesFromSynbio_Ref};
    foreach my $synbio_gene (@synbio_genes) {
      my $symbol = $synbio_gene->[0];
      my $identifier = $synbio_gene->[1];
      print "Checking for expression results for $identifier\n" if $debug;

      my ($geneRef, $expressionRef) = expressionResults($identifier, $org_short);

      if ($expressionRef) {
	@synbio_expr_results = @$expressionRef;
      }
    }

  } else {
    print "No BLAST results at: ", $perc, " percent identity\n";
  }

  unlink "$work_dir/tmp_file.txt";
  
  my $gene_start = @{ $synbio_expr_results[0] }[6];
  my $gene_end = @{ $synbio_expr_results[0] }[7];
  my $gene_strand = @{ $synbio_expr_results[0] }[8];
  my $organism_shortname = @{ $synbio_expr_results[0] }[9];
  my $taxon = @{ $synbio_expr_results[0] }[10];
  my $data_set = @{ $synbio_expr_results[0] }[11];

  my %processed = map {$_->[1] => {log2_fold_change => $_->[2], log2_mean_expression => $_->[3], variation_cooefficient => $_->[4]}} @$expressionRef;

  print "All done... Generating message\n" if $debug;

  my $synbio_result = {
    'message' => [
        { message_name => "Provenance information for part: $part_name",
	  message_publisher => "SynBioMine",
	  message_topic => "Provenance",
	  message_description => "Expression data for native part from: $organism_shortname", 
	  message_date => {
	    'part' => [
	      { type => 'promoter',  
		name => $part_name, 
		sequence => $part_sequence },
	    ],
	    'genome_hit' => [
	      { genome_hit => \1,  
		organism => $organism_shortname, 
		taxonId => $taxon,
		genome_location =>
			{ chromosome => $chromosome,
			  org_start => $organism_start,
			  org_end => $organism_end,
			  org_strand => $organism_strand },
		blast_results => $blast_out,
	      },
	    ],
	    'synbiomine_search' => [
	      {
		gene_hit => \1, 
		gene_id => $gene_from_synbio,
		gene_location =>
			{ chromosome => $chromosome,
			  gene_start => $gene_start,
			  gene_end => $gene_end,
			  gene_strand => $gene_strand },
		data_set => $data_set,  
		expression_hit => \1, 
		expression_result => \%processed,
	      }
	    ],
	},
    },
  ]
 };

my $json_text = encode_json $synbio_result;

say $json_text;

}



sub datasheet_synbis {
  my $message = shift;
  my ($part, $URI) = split("\t", $message);
  $URI =~ /http:\/\/synbis.bg.ic.ac.uk\/synbis\/.+dsid=(.+)/;
  my $dsid = $1;

  # Get the Published Part name & sequence from SynBis
  my $response = &getSeq($dsid);
  my ($id, $name, $seq, $rest) = split("\&", $response, 4);
  $id =~ s/biopart\.id\=//;
  $name =~ s/biopart\.name\=//;
  $seq =~ s/biopart\.sequence\=//;

  unless ($seq) { die "Error: no sequence for part $name\n"; }
  unless ($name eq $part) { die "Error: part names $part:$name do not match!\n"; }
  return ($name, $seq);
}

sub part_newcastle {
  my $message = shift;
  my @lines = split("\n", $message);
#  my $messg_seq_part = $lines[-2]; 
#  my $messg_descrip = $lines[-1]; 

  my $messg_seq_part = $lines[-4]; 
  my $messg_descrip = $lines[-3]; 

  $messg_seq_part =~ /sequence=(.+)/;
  my $seq = $1;

#  print "MSG:", $messg_seq_part, "\n"; ###
  
  my ($name, $uri) = split("\t", $messg_descrip);
  return ($name, $seq);

}

sub getSeq {
  my $id = shift;
  my $base = "http://cambridge:Punting654\@synbis.bg.ic.ac.uk/synbis/PartDatasheet?dsid=";

  my $url = "$base$id";

  my $agent = LWP::UserAgent->new;

  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);

#  die "Error: ", $response->header('WWW-Authenticate') || 
#    'Error accessing',
    #  ('WWW-Authenticate' is the realm-name)
#    "\n ", $response->status_line, "\n at $url\n Aborting"
#   unless $response->is_success;

  $response->is_success or print "$id\tError: " . 
  $response->code . " " . $response->message, "\n";
  return $response->content;

}


