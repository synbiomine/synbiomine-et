#!/usr/bin/perl

use strict;
use warnings;
use File::Spec::Functions;
use Getopt::Std;
use Net::FTP;
use LWP::UserAgent;
use HTTP::Date;
use Term::ANSIColor qw(:constants);
use Time::localtime;

use IO::Uncompress::Gunzip qw(:all);

use feature ':5.12';

my $current_symlink = "current";
my $selected_genomes_fn = "synbiomine_selected_assembly_summary_refseq.txt";

my $usage = "Usage:fetchSynbioData.pl [-hv] data_directory

Data download script for SynBioMine.
The data directory needs to contain sub-directories named:
uniprot
kegg
genbank
go-annotation
taxons

It makes a new sub-directory under each with that day's date: dd_mm_yyyy

Retrieves from NCBI (ftp.ncbi.nlm.nih.gov) and writes to genbank directory
\tChromosome fasta (.fna)
\tRefSeq annotation (.gff)
\tassembly report (_report.txt)

Retrieves from UniProt (www.uniprot.org) and writes to uniprot directory
\tSwissProt proteins (taxonID_uniprot_sprot.xml)
\tTrEMBL proteins (taxonID_uniprot_trembl.xml)

Retrieves from EBI GO proteomes (ftp.ebi.ac.uk) and writes to go-annotation directory
Fetch and parse proteome2taxid file to get taxon to proteome ID mappings
\tproteomID.orgShortname.goa : proteome GO annotations

Uses taxon ID to query KEGG webservices (www.genome.jp) and writes to kegg directory
and retrieves KEGG organism three-letter codes. In the kegg directory it writes:
\tkegg_org.txt   : file of three_letter_org_codes - used to get pathways
\tkegg_taxa.txt  : info for kegg_config.properties

kegg_org.txt is needed for kegg_org_pathway_doc.pl to get pathways.

The script also generates a string of taxon IDs which it writes to the taxons dir.
The taxon IDs are needed by other data sources in the project.xml e.g. pubmed-gene

options:
\t-h\tthis usage
\t-v\tmore verbose logging

";

my @errors = ();

my (%opts, $verbose);

getopts('hv', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"v"} and $verbose = 1;

#my $base = "/SAN_synbiomine/data/";
@ARGV > 0 or die $usage;
my $base = $ARGV[0];

# email addr is required for NCBI FTP use
my $contact = 'justincc@intermine.org'; # Please set your email address here to help us debug in case of problems.
my $agent = LWP::UserAgent->new(agent => "libwww-perl $contact");

# Global FTP params
$ENV{FTP_PASSIVE} = 1;
my $timeout      = 15;
#my $retries      = 5;
my $username = 'anonymous'; # allow anonymous FTPO with email addr as pwd
my $password = 'justincc@intermine.org'; # required

# set ftp address for ncbi
my $hostname = 'ftp.ncbi.nlm.nih.gov';
my $genbank_dir = catdir($base, "genbank");

log_new_activity("Loading previously selected assembly summary data");

###while (<$handle>) { ### if we want all the bacteria we'd probably use this loop

# We will populate this with data for ftp access later
my $selectedAssemPath = catdir($genbank_dir, $selected_genomes_fn);
open SELECTED_ASSEM, $selectedAssemPath or die "Could not open $selectedAssemPath for reading: $!";
my @assem = <SELECTED_ASSEM>;
close SELECTED_ASSEM;

my %org_taxon;

for (@assem) {
  chomp;

  my($assembly_id, $bioproject, $biosample, $wgs_master, $refseq_category, $taxid, 
    $species_taxid, $organism_name, $infraspecific_name, $isolate, $version_status, 
    $assembly_level, $release_type, $genome_rep, $seq_rel_date, $asm_name, 
    $submitter, $gbrs_paired_asm, $paired_asm_comp) = split("\t", $_);

#  say "Found selected $taxid => $assembly_id, $organism_name" if ($verbose);

  # There's a strange Bacillus species that has [] around its name!
  # [Bacillus] selenitireducens MLS10
  $organism_name =~ s/\[/_/;
  $organism_name =~ s/\]//;

  # We're going to construct the directories used to download GFF & fna files
  my $assembly_vers = $assembly_id . "_" . $asm_name;
  my $assembly_ftp_dir = "all_assembly_versions/" . $assembly_vers;

  my $species;

  # they've probably made it more complicated than it needs to be so we have to define
  # rules on whether the directory is Genus_species or if it covers a species sp.
  if ($organism_name =~ / sp\. /) {
    $organism_name =~ /(.+)/; # grab the whole thing if it's Genus sp.
    $species = $1;
  }
  else {
    $organism_name =~ /(\w+ \w+)/; # otherwise grab genus_species
    $species = $1;
  }

  $species =~ s/ /_/g; # replace spaces with underscore

  # store the data to use for FTP access later
  $org_taxon{$taxid} = [$species, $assembly_vers, $refseq_category, $assembly_ftp_dir]; 
}

# Do this in sorted order
for my $key (sort {$a <=> $b} keys %org_taxon) {
  say "Found selected $key => " . join(", ", @{$org_taxon{$key}});
}

say "Found " . scalar(keys %org_taxon) . " selected assemblies";

log_new_activity("Downloading EBI taxon ID -> GOA map");

my $ebi_hostname = 'ftp.ebi.ac.uk';

# Hardcode the directory and filename we want to get
my $ebi_home = '/pub/databases/GO/goa/proteomes'; 
my $ebi_file = 'proteome2taxid'; # this is where we get the look-up file that maps GO proteome to organism

my $go_dir = catdir($base, "go-annotation");

# say "Trying FTP for: $ebi_hostname";
my $ftp3 = Net::FTP->new($ebi_hostname, BlockSize => 20480, Timeout => $timeout);
defined($ftp3) or die "Could not connect to $ebi_hostname: $!";

$ftp3->login($username, $password) or die "Cannot login ", $ftp3->message; 
$ftp3->cwd($ebi_home) or die "Cannot change working directory ", $ftp3->message;

my $go_ref = fetch_filtered_data($ftp3, $ebi_file, catdir($go_dir, $ebi_file));
my @go_taxons = @{ $go_ref };

my %GO_proteomes; # Make a look-up of tax id to GO proteome
for my $go_proteome (@go_taxons) {
  chomp $go_proteome;
  my ($org, $tax, $proteome) = split("\t", $go_proteome);
  $GO_proteomes{$tax} = $proteome;
}

# say join("\n", @go_taxons);

log_new_activity("Downloading GO annotation files for organisms");

$ftp3->ascii or die "Cannot set ascii mode: " . $ftp3->message; # set ascii mode for non-binary otherwise you get errors 

# Loop through the taxon IDs and download the GO annotation file (.goa)
for my $key (sort {$a <=> $b} keys %org_taxon) {

# Check to see if our strains have GO annotations (look-up on tax ID)
  if (exists $GO_proteomes{$key} ) {

# if yes, we're going to download the file
    my $go_file = $GO_proteomes{$key}; 

    say "Fetching: $key => $go_file";

    fetch_file($ftp3, $go_file, catdir($go_dir, $go_file));
  } else {
    say "No GO annotation found for taxon ID $key";
  }
}

##################

log_new_activity("Downloading UniProt summary files");

my $unip_dir = catdir($base, "uniprot");
my $unip_kb_ftp_path = "/pub/databases/uniprot/current_release/knowledgebase/complete";
my $unip_kb_docs_ftp_path = "$unip_kb_ftp_path/docs";

my $unip_splice_gz_ftp_path = "$unip_kb_ftp_path/uniprot_sprot_varsplic.fasta.gz";
my $unip_splice_dest_path = catdir($unip_dir, "uniprot_sprot_varsplic.fasta");

my $unip_xsd_bn = "uniprot.xsd";
my $unip_xsd_ftp_path = "$unip_kb_ftp_path/$unip_xsd_bn";
my $unip_xsd_path = catdir($unip_dir, $unip_xsd_bn);

my $unip_kw_ftp_path = "$unip_kb_docs_ftp_path/keywlist.xml.gz";
my $unip_kw_path = catdir($unip_dir, "keywlist.xml");

# log_new_activity("Fetching to $unip_splice_dest_path");

my $retr_spli_fh = fetch_fh($ftp3, $unip_splice_gz_ftp_path);
gunzip_fh($retr_spli_fh, $unip_splice_dest_path);

# log_new_activity("Fetching to $unip_xsd_path");
fetch_file($ftp3, $unip_xsd_ftp_path, $unip_xsd_path);

# log_new_activity("Fetching to $unip_kw_path");
my $retr_kw_fh = fetch_fh($ftp3, $unip_kw_ftp_path);
gunzip_fh($retr_kw_fh, $unip_kw_path);

$ftp3->quit;

##################

log_new_activity("Downloading NCBI FASTA, GFF and assembly reports");

# Now... FTP to NCBI genomes to get chromosome fasta (.fna) and refseq annotations (.gff)
my $refseq = '/genomes/refseq/bacteria'; # used for path

my $ftp2 = Net::FTP->new($hostname, BlockSize => 20480, Timeout => $timeout);
defined($ftp2) or die "Could not connect to $hostname: $!";

$ftp2->login($username, $password) or die "Cannot login ", $ftp2->message;

# Loop through the taxon IDs and download the GFF, chrm fasta and the report file
for my $key (sort {$a <=> $b} keys %org_taxon) {

  # Make a directory for each genbank organism
  my ($species, $assembly_vers, $refseq_category, $assembly_ftp_dir) = @{ $org_taxon{$key} };
  my $assembly_dir = catdir($genbank_dir, $assembly_vers);

  if (-d $assembly_dir) {
    my $assemblyReportPath = catdir($assembly_dir, "${assembly_vers}_assembly_report.txt");
    my $assemblyFastaPath = catdir($assembly_dir, "${assembly_vers}_genomic.fna");
    my $assemblyGffPath = catdir($assembly_dir, "${assembly_vers}_genomic.gff");

    if (-e $assemblyReportPath and -e $assemblyFastaPath and -e $assemblyGffPath) {
      say "Using existing files for $key => $species";
      next;
    }
  }

  mkdir $assembly_dir, 0755;

  my $refseq_path = "$refseq/$species/$assembly_ftp_dir";

  if (not $ftp2->cwd($refseq_path)) {
    say "No FTP directory $key => $refseq_path.  Skipping";
    next;
  }

  say "Fetching files for $key => $refseq_path";

# get a list of the matching files
  my @file_list = grep /\.gff.gz|\.fna.gz|_report.txt/, $ftp2->ls();

# loop through the file list and download them to the relevant organsims genbank directory
  for my $gb_file (@file_list) {
    # say "Processing FILE: ", $gb_file;

    if ($gb_file =~ /\.gz/) {
      $gb_file =~ /(.+)\.gz/;
      my $raw = $1;

      $ftp2->binary or die "Cannot set binary mode: $!"; # binary mode for the zip file
      # say "Fetch and unzip: $gb_file --> $raw"; # fetch and unzip

      my $retr_fh = $ftp2->retr($gb_file) or log_error("Problem with $refseq_path\nCannot retrieve $gb_file");

      if ($retr_fh) {
        gunzip $retr_fh => "$genbank_dir/$assembly_vers/$raw", AutoClose => 1
          or log_error("Zip error $refseq_path\nCannot uncompress '$gb_file': $GunzipError");
        # say "Success - adding: $genbank_dir/$date_dir/$assembly_vers/$raw";
      }
      else {
        say "Darn! Problem with $refseq_path\nCouldn't get $gb_file";
        next;
      }
    } else {
      $ftp2->ascii or die "Cannot set ascii mode: $!"; # set ascii mode for non-binary otherwise you get errors 

      # say "Fetching: $gb_file";

      $ftp2->get($gb_file, "$genbank_dir/$assembly_vers/$gb_file")
	      or log_error("Problem with $refseq_path\n\nCannot retrieve $gb_file");
    }
  }
}

$ftp2->quit;

log_new_activity("Adding reference proteomes");

# Add reference proteomes - not real strains so there's no genome sequence
add_taxon(\%org_taxon, 1392, "reference model 1392 - no genome sequence"); # Bacillus anthracis
add_taxon(\%org_taxon, 83333, "reference model 83333 - no genome sequence"); # E Coli strain K12

log_new_activity("Performing rest of work");

# process KEGG and fetch UniProt protein files
my $kegg_dir = $base . "/kegg";
# kegg_org.txt is list of organism acronyms; kegg_taxa.txt is the kegg config file
open (KEGG_ORG_OUT, ">$kegg_dir/kegg_org.txt") or die "Can't write file: $kegg_dir/kegg_org.txt: $!\n";
open (KEGG_TAXA_OUT, ">$kegg_dir/kegg_taxa.txt") or die "Can't write file: $kegg_dir/kegg_taxa.txt: $!\n";

# set up the taxons directory
my $taxon_dir = $base . "/taxons";
open (TAXON_OUT, ">$taxon_dir/taxons.txt") or die "Can't write file: $taxon_dir/taxons.txt: $!\n";

my @taxa;
for my $taxon (sort {$a <=> $b} keys %org_taxon) {
  # say "$key: " . join(" * ", @{$org_taxon{$key}}); # for debug

  push (@taxa, $taxon); # store the taxon IDs to write to file later
}

say TAXON_OUT join(" ", @taxa); # write tax IDs - needed for some data sources in project.xml
close TAXON_OUT;

my $reference = 'reviewed:yes'; # proteomes which usually have some curation
my $complete = 'reviewed:no'; # proteomes whith mostly automated annotation

# extensions for filenames
my $db_sp = "uniprot_sprot"; 
my $db_tr = "uniprot_trembl";

for my $taxon (@taxa) {
  # say "$key: " . join(" * ", @{$org_taxon{$key}}); # for debug

  say "### Processing taxon: $taxon ###";

  kegg_dbget($taxon); # send the taxon ID to the KEGG search subroutine - get the org acronym

# Send the Taxon IDs to the UniProt subroutine to get the proteins
  query_uniprot($db_sp, $taxon, $reference); # Get swissprot
  query_uniprot($db_tr, $taxon, $complete); # Get TrEMBL
  
  print "\n";
}

# Close the out files
close (KEGG_ORG_OUT);
close (KEGG_TAXA_OUT);

scalar(@errors) and print RED;
say "Finished with " . scalar(@errors) . " errors";
scalar(@errors) and print RESET;

##############################
######## SUBROUTINES #########
##############################

=pod
Subroutine user agent to connect to UniProt
=cut
sub query_uniprot {

  my ($db, $taxon, $reference) = @_;

# Alternative formats: html | tab | xls | fasta | gff | txt | xml | rdf | list | rss
  my $file = $base . "/uniprot/". $taxon . "_" . $db . '.xml';
  my $query_taxon = "http://www.uniprot.org/uniprot/?query=organism:$taxon+$reference&format=xml&include=yes";

  my $response_taxon = $agent->mirror($query_taxon, $file);

  if ($response_taxon->is_success) {

# Check the header for results
    my $results = $response_taxon->header('X-Total-Results');
    unless ($results) {
      if ($db =~ /sprot/) {
        say "No SwissProt results for $taxon";
        unlink $file; # unlink - if the file doesn't exist
      }
      else {
        say "No TrEMBL results for $taxon";
        unlink $file; # unlink - if the file doesn't exist
      }

      return;
    }

# Check the timestamps to see if the server data is newer
    my $release = $response_taxon->header('X-UniProt-Release');
    my $date = sprintf("%4d-%02d-%02d", HTTP::Date::parse_date($response_taxon->header('Last-Modified')));

    say "Fetched $results entries in UniProt release $release ($date) for $db";

    # say "Success for Taxon: $taxon with $db";
    # say "File $file: downloaded $results entries of UniProt release $release ($date)";
    # say "\n";
  }
  elsif ($response_taxon->code == HTTP::Status::RC_NOT_MODIFIED) {
    say "File $file: up-to-date"; # if it's not newer, don't download
  }
  else {
    log_error('Failed, got ' . $response_taxon->status_line .
      ' for ' . $response_taxon->request->uri);
  }
}

=pod
# Search KEGG to get three-letter kegg org codes
# Use the taxon ID to query KEGG's WS (using dbget) - I can't believe there's no taxon look-up!
=cut
sub kegg_dbget {

  my $taxon = shift;

# WS URL for search
  my $url = "http://www.genome.jp/dbget-bin/www_bfind_sub?dbkey=genome&keywords=$taxon&mode=bfind&max_hit=5";

  my $request  = HTTP::Request->new(GET => $url); # Form the request object
  my $response = $agent->request($request); # submit the request

# Check the response
  $response->is_success or say "Error: " . $response->code . " " . $response->message;

  my $content = $response->content;

  # say "Response '$content'";

  open my ($str_fh), '+<', \$content;

# Parse the response and check to see if any match the taxon ID
  my @elements;
  while (<$str_fh>) {
    chomp;

    if ($_ =~ /www_bget\?genome/) {
      @elements = split("\>", $_);
    }
  }

  close ($str_fh);

# if we match the taxon ID, add the line to the array
  my @matches = grep /$taxon\;/, @elements;

#      say $_;
  if (@matches) {
    my $kegg_info = $matches[0];

    $kegg_info =~ s/^ //g;
    $kegg_info =~ s/\<.+//g;
    $kegg_info =~ s/\;/,/;

    my ($tla, $uniprot, $kegg_taxon, $org_name) = split(", ", $kegg_info);
  # some entries don't have Uniprot IDs, so...
    unless ($uniprot =~ /[A-Z]/) {
      $org_name = $kegg_taxon;
      $kegg_taxon = $uniprot;
    }
    $org_name =~ s/ \(.+\)$//g;

    say "Found kegg org code $tla";
    # say "out: $tla, $kegg_taxon, $org_name";
    say KEGG_ORG_OUT $tla; # Write out space-separated taxons for use in project.xml fields
    say KEGG_TAXA_OUT $tla . ".taxonId = " . $kegg_taxon; # write to KEGG config file
  }
}

=pod
Add a taxon that just has a description 
=cut
sub add_taxon {
  my ($taxons, $taxon_id, $taxon_description) = @_;

  say "Adding taxon $taxon_id => $taxon_description";

  $taxons->{$taxon_id} = $taxon_description;
}

=pod
Return FTP data where lines have t omatch Bacillus|Escherichia|Geobacillus
=cut
sub fetch_filtered_data {

  my ($ftp, $src, $dest) = @_;

  if (-e $dest) {
    say "Using existing file $dest";
  } else {
    #my @dir_list = grep /_uid/, $ftp->ls();

    # We're using a filehandle on the basis that it is more memory efficient as we can discard each
    # retrieved line after processing instead of slurping in the whole file at once
    #my $handle = $ftp->retr($file) or die "get failed ", $ftp->message;
    $ftp->get($src, $dest) or die "Failed to get $src for $dest: $ftp->message";
  }

  return get_filtered_data_from_file($dest);
}

=pod
Read a file and return lines that meet hard-coded criteria
=cut
sub get_filtered_data_from_file {
  my ($src) = @_;

  open(my $handle, "<", $src) or die "Could not open $src for reading: $!";

  # just grab the three Genera that we want
  my @entries = grep /Bacillus|Escherichia|Geobacillus/, <$handle>;

  # justincc 20150612 Ignoring phages and viruses as these are unlikely to be useful but need to check
  @entries = grep !/phage|virus/, @entries;

  close ($handle);

  return \@entries;
}

=pod
Fetch the given file
=cut
sub fetch_file {
  my ($ftp, $ftp_path, $to_path, $use_ascii) = @_;

  if (-e $to_path) {
    say "Using existing file $to_path";
    return 1;
  } else {
    set_ftp_transfer_mode($ftp, $use_ascii);

    return $ftp->get($ftp_path, $to_path)
  }
}

=pod
Fetch the given file as a filehandle.
Returns the filehandle on success
=cut
sub fetch_fh {
  my ($ftp, $ftp_path, $use_ascii) = @_;

  set_ftp_transfer_mode($ftp, $use_ascii);

  my $fh = $ftp->retr($ftp_path) or die "Cannot retrieve $ftp_path: $!\n";

  return $fh;
}

=pod
Gunzip the given filehandle
=cut
sub gunzip_fh {
  my ($fh, $to_path) = @_;

  return gunzip $fh => $to_path, AutoClose => 1 or die "Could not gunzip $fh: $GunzipError\n";
}

sub set_ftp_transfer_mode {
  my ($ftp, $use_ascii) = @_;

  if ($use_ascii) {
    $ftp->ascii or die "Cannot set ascii mode: ", $ftp->message;
  } else {
    $ftp->binary or die "Cannot set binary mode: ", $ftp->message;
  }
}

=pod
Provide an eye-catching way of showing when we engage in different activities in this script.
=cut
sub log_new_activity {
  my ($activity) = @_;

  say "~~~ $activity ~~~";
}

=pod
Log a non-fatal error and record to a list of errors
=cut
sub log_error {
  my ($error) = @_;

  say STDERR RED, "ERROR: $error", RESET;
  push (@errors, $error);
}
