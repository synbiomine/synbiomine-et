#!/usr/bin/perl

# requires apt-get install ncbi-blast+

#use strict;
use warnings;

use feature ':5.12';

package BlastSynbio;

require Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(run_BLAST);

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

# my $id = "test1";
# my $seq = "TTTTACTTCTAATATTTAGTGTTATAATA";
# my $len = length($seq);
# my $query = ">$id\n$seq";
# my $region_ref = &run_BLAST($query, $len);

# Set working directory
# my $work_dir = "/SAN_synbiomine/data/SYNBIO_data/BLAST/Bsub168";

sub run_BLAST {

  my ($query, $len, $work_dir, $debug) = @_;

  ### TEST DATA ###
  #my $query = ">test1\natgcagaccccgcacattcttatcgttgaagacgagttggtaacacg"; # test seq
  #my $query = ">test2\natgctgcggggcattcaaaattgaagaaaaggtaacacg"; # test fail seq
  # >nlpD\nTTCAGTAGGGTGCCTTGCACGGTAATTATGTCACTGG
  # >gcvR\nTTGTATGCATGTTTTTTTTATGCTTTCCTTAAGAACA";

  # write query to a tmp file
  open TMP_FILE, ">$work_dir/tmp_file.fa" or die $!; 
  say TMP_FILE $query;
  close TMP_FILE;

  # set BLAST params: for short seq -task blastn-short; turn off low complexity filter: -dust no
  my $blast_db = "$work_dir/Bsubtilis_168_refSeq";
  my $blast_out;

  if ($len <= 30) {
    warn "SHORT sequence ($len) - using blastn-short $query\n" if ($debug);
    $blast_out = `blastn -query $work_dir/tmp_file.fa -db $blast_db -task blastn-short -evalue 1e-1 -dust no -ungapped -outfmt 6`;
  }
  else {
    $blast_out = `blastn -query $work_dir/tmp_file.fa -db $blast_db -evalue 1e-1 -dust no -ungapped -outfmt 6`;
  }

  say "Blast res: ", $blast_out if ($debug); ###

  my @blast_res;
  if ($blast_out =~ m/\n/) {
    @blast_res = split("\n", $blast_out);
  } else {
    push(@blast_res, $blast_out);
  }
  #say join("\n", @blast_res), "\n";

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

  my @regions;
  for my $result (@blast_res) {
    my ($q_name, $targ, $perc, $a_len, $mism, $gap, 
      + $q_start, $q_end, $db_start, $db_end, $other) = split("\t", $result, 11);

  unlink "$work_dir/tmp_file.txt";

  # Test to see if we have results
    unless ($perc) {
      warn "No BLAST hits for QUERY: $query\n" if ($debug);
      return;
    }

  # grab host chromosome info ready for synbiomine query
    my $chromosome;
    if ($targ =~ /\|(NC_.+)\|/) {
      $chromosome = $1;
    } else {
      warn "No Chromosome found for $targ\n" if ($debug);
      return;
    }

  # query region co-ordinates
    my ($organism_start, $organism_end, $organism_strand);

  # check co-ord to get strand info
    if ($db_start < $db_end) {
      $organism_start = $db_start;
      $organism_end = $db_end;
      $organism_strand = "1";
    } else {
      $organism_start = $db_end;
      $organism_end = $db_start;
      $organism_strand = "-1";
    }

    my $region = "$chromosome:$organism_start..$organism_end $organism_strand";
    say "$region" if ($debug);

    if ($a_len != $len) {
      warn "Partial match: $q_name match length ($a_len) less than query length ($len)\n" if ($debug);
      return \@regions;
    }

    if ($perc > 95) {
      push(@regions, $region);
      say "BlastRes used: ", $result if ($debug);
    } else {
      warn "$q_name: BLAST hit for $region below cutoff: ", $perc, " percent identity\n" if ($debug);
      return \@regions;
    }
  }
  return \@regions;
}
1;
