#!/usr/bin/perl

use strict;
use warnings;
use File::Spec::Functions;
use Getopt::Std;
use Net::FTP;
#use Net::FTP::AutoReconnect;
use LWP::UserAgent;
use HTTP::Date;
use Time::localtime;

use IO::Uncompress::Gunzip qw(:all);

use feature ':5.12';

my $current_symlink = "current";
my @sources = qw(genbank go-annotation kegg taxons uniprot);

my $usage = "Usage:fetchSynbioData.pl [-h] data_directory

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

";

my (%opts);

getopts('h', \%opts);
defined $opts{"h"} and die $usage;

# date settings - used to make a new working folder
my $tm = localtime;
my ($DAY, $MONTH, $YEAR) = ($tm->mday, ($tm->mon)+1, ($tm->year)+1900);

#my $base = "/SAN_synbiomine/data/";
@ARGV > 0 or die "data_directory must be specified.\n";
my $base = $ARGV[0];

notify_new_activity("Creating data directory structure at [$base]");

if (not -d $base) {
  mkdir $base, 0755 or die "Could not create data_directory $base: $!\n";
}

my $date_dir  = $DAY . "_" . $MONTH . "_" . $YEAR;

# make a new date directory under each of the data directories
foreach my $source (@sources) {

  my $source_dir = catdir($base, $source);

  if (not -d $source_dir) {
    mkdir "$source_dir", 0755 or die "Could not make $source_dir: $!\n";
  }

  my $source_date_dir = catdir($source_dir, $date_dir);

  -d $source_date_dir and die "$source_date_dir already exists.  Aborting.\n";
  mkdir $source_date_dir, 0755 or die "Could not make $source_date_dir.  Aborting.\n";

  my $source_current_symlink = catdir($source_dir, $current_symlink);

  if (-e $source_current_symlink) {
    if (-l $source_current_symlink) {
      unlink $source_current_symlink or die "Failed to remove symlink $source_current_symlink: $!\n";
    } else {
      die "$source_current_symlink is unexpectedly not a symlink!  Aborting.\n";
    }
  }

  #symlink $source_date_dir, $current_symlink or die "Failed to link $source_date_dir with $source_current_symlink: $!\n";
  symlink $date_dir, $source_current_symlink or die "Failed to link $source_date_dir with $source_current_symlink: $!\n";
}

notify_new_activity("Downloading EBI taxon ID -> GOA map");

# email addr is required for NCBI FTP use
my $contact = 'justincc@intermine.org'; # Please set your email address here to help us debug in case of problems.
my $agent = LWP::UserAgent->new(agent => "libwww-perl $contact");

# Global FTP params
$ENV{FTP_PASSIVE} = 1;
my $timeout      = 600;     # seconds, default is 120
#my $retries      = 5;
my $username = 'anonymous'; # allow anonymous FTPO with email addr as pwd
my $password = 'justincc@intermine.org'; # required

# set ftp address for EBI GO server
my $ebi_hostname = 'ftp.ebi.ac.uk';

# Hardcode the directory and filename we want to get
my $ebi_home = '/pub/databases/GO/goa/proteomes'; 
my $ebi_file = 'proteome2taxid'; # this is where we get the look-up file that maps GO proteome to organism

my $go_ref = &fetch_filtered_data($ebi_hostname, $ebi_home, $ebi_file, $username, $password);
my @go_taxons = @{ $go_ref };

my %GO_proteomes; # Make a look-up of tax id to GO proteome
for my $go_proteome (@go_taxons) {
  chomp $go_proteome;
  my ($org, $tax, $proteome) = split("\t", $go_proteome);
  $GO_proteomes{$tax} = $proteome;
}

# say join("\n", @go_taxons);

notify_new_activity("Downloading NCBI assembly summary");

# set ftp address for ncbi
my $hostname = 'ftp.ncbi.nlm.nih.gov';

# Hardcode the directory and filename we want to get
my $home = '/genomes/ASSEMBLY_REPORTS'; 
my $file = 'assembly_summary_refseq.txt'; # this is where we get the look-up file that maps assembly ID to organism

my $assem_ref = &fetch_filtered_data($hostname, $home, $file, $username, $password);
my @assem = @{ $assem_ref };

notify_new_activity("Constructing download file information");

###while (<$handle>) { ### if we want all the bacteria we'd probably use this loop

my %org_taxon;

# just process the three genera
for (@assem) {
  chomp;

  my($assembly_id, $bioproject, $biosample, $wgs_master, $refseq_category, $taxid, 
    $species_taxid, $organism_name, $infraspecific_name, $isolate, $version_status, 
    $assembly_level, $release_type, $genome_rep, $seq_rel_date, $asm_name, 
    $submitter, $gbrs_paired_asm, $paired_asm_comp) = split("\t", $_);

# We're only interested in reference or representative genomes - complete and probably have refseq annotations
# they used to use hyphen, now they use space so check for both in case they change back
  next unless ( ($refseq_category) && ($refseq_category =~ /-genome| genome/) ); 

# There's a strange Bacillus species that has [] around its name!
# [Bacillus] selenitireducens MLS10
  $organism_name =~ s/\[/_/;
  $organism_name =~ s/\]//;

# We want the chromosome data
  if ($assembly_level =~ /Chromosome/) {

    say $_; # so we can see what's going on - redirect

# We're going to construct the directories used to download GFF & fna files
    my $assembly_vers = $assembly_id . "_" . $asm_name;
    my $assembly_dir = "all_assembly_versions/" . $assembly_vers;

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

# there are some duplicate entries - check whether we've seen it before
    if ( exists $org_taxon{$taxid} ) {
    # For B. subtilis 168 we want the representative genome - the reference genome has odd IDs
      if ( ($taxid eq '224308') and ($refseq_category =~ /reference-genome/) ) {
	      next;
      }
      elsif ($refseq_category =~ /representative-genome/) {
	      next;
      }
    }

  # store the data to use for FTP access later
    $org_taxon{$taxid} = [$species, $assembly_vers, $refseq_category, $assembly_dir]; 
  }
}

### Now... Process GO proteomes to get GO annotations ###
my $go_dir = catdir($base, "go-annotation");

# But, while we're logged in we'll get some of extra uniprot files
my $unip_dir = catdir($base, "uniprot");
my $unip_kb_ftp_path = "/pub/databases/uniprot/current_release/knowledgebase/complete";
# my $unip_xtra_dir = "/pub/databases/uniprot/current_release/knowledgebase/complete";
# my $unip_xtra_ftp_path = "/pub/databases/uniprot/current_release/knowledgebase/complete";
my $unip_kb_docs_ftp_path = "$unip_kb_ftp_path/docs";

my $unip_splice_gz_ftp_path = "$unip_kb_ftp_path/uniprot_sprot_varsplic.fasta.gz";
my $unip_splice_dest_path = catdir($unip_dir, $date_dir, "uniprot_sprot_varsplic.fasta");

my $unip_xsd_bn = "uniprot.xsd";
my $unip_xsd_ftp_path = "$unip_kb_ftp_path/$unip_xsd_bn";
my $unip_xsd_path = catdir($unip_dir, $date_dir, $unip_xsd_bn);

my $unip_kw_ftp_path = "$unip_kb_docs_ftp_path/keywlist.xml.gz";
my $unip_kw_path = catdir($unip_dir, $date_dir, "keywlist.xml");

notify_new_activity("Fetching to $unip_splice_dest_path");

my $ftp3 = Net::FTP->new($ebi_hostname, BlockSize => 20480, Timeout => $timeout);

$ftp3->login($username, $password) or die "Cannot login ", $ftp3->message; 

my $retr_spli_fh = fetch_fh($ftp3, $unip_splice_gz_ftp_path, 0);
gunzip_fh($retr_spli_fh, $unip_splice_dest_path) or die "Could not gunzip to $unip_splice_dest_path: $GunzipError\n";

notify_new_activity("Fetching to $unip_xsd_path");
fetch_file($ftp3, $unip_xsd_ftp_path, $unip_xsd_path, 0) or die "Cannot retrieve $unip_xsd_ftp_path: $!\n";

notify_new_activity("Fetching to $unip_kw_path");
my $retr_kw_fh = fetch_fh($ftp3, $unip_kw_ftp_path, 0);
gunzip_fh($retr_kw_fh, $unip_kw_path) or die "Could not gunzip to $unip_kw_path: $GunzipError\n";

notify_new_activity("Performing rest of work");

# Switch to the GO anotation dir to fetch those files
# say "Trying FTP for: $ebi_hostname";

$ftp3->cwd($ebi_home) or die "Cannot change working directory ", $ftp3->message;

# Loop through the taxon IDs and download the GO annotation file (.goa)
for my $key (keys %org_taxon) {

# Check to see if our strains have GO annotations (look-up on tax ID)
  if (exists $GO_proteomes{$key} ) {

# if yes, we're going download the file
    my $go_file = $GO_proteomes{$key}; 

    say "Processing FILE: ", $go_file;

    say "Fetching: $go_file";
    $ftp3->ascii or die "Cannot set ascii mode: $!"; # set ascii mode for non-binary otherwise you get errors 

    $ftp3->get($go_file, "$go_dir/$date_dir/$go_file")
      or warn "Problem with $ebi_home\nCannot retrieve $go_file\n";
  } else {
    say "No GO annotation found for $key";
  }
}

$ftp3->quit;

##################

# Now... FTP to NCBI genomes to get chromosome fasta (.fna) and refseq annotations (.gff)
my $refseq = '/genomes/refseq/bacteria'; # used for path
my $genbank_dir = $base . "/genbank";

my $ftp2 = Net::FTP->new($hostname, BlockSize => 20480, Timeout => $timeout);

$ftp2->login($username, $password) or die "Cannot login ", $ftp2->message;

# Loop through the taxon IDs and download the GFF, chrm fasta and the report file
for my $key (keys %org_taxon) {

# Make a directory for each genbank organism
  my ($species, $assembly_vers, $refseq_category, $assembly_dir) = @{ $org_taxon{$key} };
  mkdir "$genbank_dir/$date_dir/$assembly_vers", 0755;

  my $refseq_path = $refseq . "/" . $species . "/" . $assembly_dir;
  say "Trying FTP for: $refseq_path";

  $ftp2->cwd("$refseq/$species/$assembly_dir") or die "Cannot change working directory ", $ftp2->message;

# get a list of the matching files
  my @file_list = grep /\.gff.gz|\.fna.gz|_report.txt/, $ftp2->ls();

# loop through the file list and download them to the relevant organsims genbank directory
  for my $gb_file (@file_list) {
    say "Processing FILE: ", $gb_file;

    if ($gb_file =~ /\.gz/) {
      $gb_file =~ /(.+)\.gz/;
      my $raw = $1;

      $ftp2->binary or die "Cannot set binary mode: $!"; # binary mode for the zip file
      say "Fetch and unzip: $gb_file --> $raw"; # fetch and unzip

      my $retr_fh = $ftp2->retr($gb_file) or warn "Problem with $refseq_path\nCannot retrieve $gb_file\n";

      if ($retr_fh) {
        gunzip $retr_fh => "$genbank_dir/$date_dir/$assembly_vers/$raw", AutoClose => 1
          or warn "Zip error $refseq_path\nCannot uncompress '$gb_file': $GunzipError\n";
        say "Success - adding: $genbank_dir/$date_dir/$assembly_vers/$raw";
      }
      else {
        say "Darn! Problem with $refseq_path\nCouldn't get $gb_file";
        next;
      }
    } else {
      $ftp2->ascii or die "Cannot set ascii mode: $!"; # set ascii mode for non-binary otherwise you get errors 

      say "Fetching: $gb_file";

      $ftp2->get($gb_file, "$genbank_dir/$date_dir/$assembly_vers/$gb_file")
	      or warn "Problem with $refseq_path\n\nCannot retrieve $gb_file\n";
    }
  }
}

$ftp2->quit;


# process KEGG and fetch UniProt protein files
my $kegg_dir = $base . "/kegg/$date_dir";
# kegg_org.txt is list of organism acronyms; kegg_taxa.txt is the kegg config file
open (KEGG_ORG_OUT, ">$kegg_dir/kegg_org.txt") or die "Can't write file: $kegg_dir/kegg_org.txt: $!\n";
open (KEGG_TAXA_OUT, ">$kegg_dir/kegg_taxa.txt") or die "Can't write file: $kegg_dir/kegg_taxa.txt: $!\n";

# set up the taxons directory
my $taxon_dir = $base . "/taxons/$date_dir";
open (TAXON_OUT, ">$taxon_dir/taxons_$date_dir.txt") or die "Can't write file: $taxon_dir/taxons_$date_dir.txt: $!\n";

my $reference = 'reviewed:yes'; # proteomes which usually have some curation
my $complete = 'reviewed:no'; # proteomes whith mostly automated annotation

# extensions for filenames
my $db_sp = "uniprot_sprot"; 
my $db_tr = "uniprot_trembl";

# Add reference proteomes - not real strains so there's no genome sequence
$org_taxon{"83333"} = ["reference model 83333 - no genome sequence"];
$org_taxon{"1392"} = ["reference model 1392 - no genome sequence"];

# Loop through the taxons again
my @taxa;
for my $key (keys %org_taxon) {
  say "\n$key: ", join(" * ", @{ $org_taxon{$key} } ); # for debug

  my $taxon = $key;
  push (@taxa, $taxon); # store the taxon IDs to write to file later

# For each taxon
  say "Processing taxon: ", $taxon;

  &kegg_dbget($taxon); # send the taxon ID to the KEGG search subroutine - get the org acronym

# Send the Taxon IDs to the UniProt subroutine to get the proteins
  &query_uniprot($db_sp, $taxon, $reference); # Get swissprot
  &query_uniprot($db_tr, $taxon, $complete); # Get TrEMBL

}

# Write the taxons to file
say TAXON_OUT join(" ", @taxa); # write tax IDs - needed for some data sources in project.xml

# Close the out files
close (KEGG_ORG_OUT);
close (KEGG_TAXA_OUT);
close (TAXON_OUT);

exit(1);

######## SUBROUTINES #########
# Subroutine user agent to connect to UniProt #
sub query_uniprot {

  my ($db, $taxon, $reference) = @_;

# Alternative formats: html | tab | xls | fasta | gff | txt | xml | rdf | list | rss
  my $file = $base . "/uniprot/$date_dir/". $taxon . "_" . $db . '.xml';
  my $query_taxon = "http://www.uniprot.org/uniprot/?query=organism:$taxon+$reference&format=xml&include=yes";

  my $response_taxon = $agent->mirror($query_taxon, $file);

  if ($response_taxon->is_success) {

# Check the header for results
    my $results = $response_taxon->header('X-Total-Results');
    unless ($results) {
      if ($db =~ /sprot/) {
        say "No SwissProt results for $taxon";
        unlink $file; # unlink - if the file doesn't exist
        return;
      }
      else {
        say "No TrEMBL results for $taxon\n";
        unlink $file; # unlink - if the file doesn't exist
        return;
      }
    }

# Check the timestamps to see if the server data is newer
    my $release = $response_taxon->header('X-UniProt-Release');
    my $date = sprintf("%4d-%02d-%02d", HTTP::Date::parse_date($response_taxon->header('Last-Modified')));
    say "Success for Taxon: $taxon with $db";
    say "File $file: downloaded $results entries of UniProt release $release ($date)";
    say "\n";
    return;
  }
  elsif ($response_taxon->code == HTTP::Status::RC_NOT_MODIFIED) {
    say "File $file: up-to-date"; # if it's not newer, don't download
  }
  else {
    warn 'Failed, got ' . $response_taxon->status_line .
      ' for ' . $response_taxon->request->uri . "\n"; # report if errors generated
  }
  return;
}

# Search KEGG to get three-letter kegg org codes
# Use the taxon ID to query KEGG's WS (using dbget) - I can't believe there's no taxon look-up!
sub kegg_dbget {

  my $taxon = shift;

# WS URL for search
  my $url = "http://www.genome.jp/dbget-bin/www_bfind_sub?dbkey=genome&keywords=$taxon&mode=bfind&max_hit=5";

  my $request  = HTTP::Request->new(GET => $url); # Form the request object
  my $response = $agent->request($request); # submit the request

# Check the response
  $response->is_success or say "Error: " . 
  $response->code . " " . $response->message;

# Grab the conetent
  my $content = $response->content;
  #say $content;

# Open content as file handle
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

    say "info: $kegg_info";
    say "out: $tla, $kegg_taxon, $org_name";
    say KEGG_ORG_OUT $tla; # Write out space-separated taxons for use in project.xml fields
    say KEGG_TAXA_OUT $tla . ".taxonId = " . $kegg_taxon; # write to KEGG config file
  }
}

=pod
Return FTP data where lines have t omatch Bacillus|Escherichia|Geobacillus
=cut
sub fetch_filtered_data {

  my ($hostname, $home, $file, $username, $password) = @_;

  # my $ftp = Net::FTP->new($hostname, BlockSize => 20480, Timeout => $timeout, Debug   => 1); # Construct FTP object
  my $ftp = Net::FTP->new($hostname, BlockSize => 20480, Timeout => $timeout);

  $ftp->login($username, $password) or die "Cannot login ", $ftp->message;

  $ftp->cwd($home) or die "Cannot change working directory ", $ftp->message;

  #my @dir_list = grep /_uid/, $ftp->ls();

  # get the assembly report file
  my $handle = $ftp->retr($file) or die "get failed ", $ftp->message;

  # just grab the three Genera that we want from the handle and slurp into an array
  my @assem = grep /Bacillus|Escherichia|Geobacillus/, <$handle>;

  ### my @assem = grep / subtilis/, <$handle>; # quick version for testing

  close ($handle);
  $ftp->quit;

  return \@assem;
}

=pod
Fetch the given file
=cut
sub fetch_file {
  my ($ftp, $ftp_path, $to_path, $use_ascii) = @_;

  set_ftp_transfer_mode($ftp, $use_ascii);

  return $ftp->get($ftp_path, $to_path)
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

  return gunzip $fh => $to_path, AutoClose => 1;
}

sub set_ftp_transfer_mode {
  my ($ftp, $use_ascii) = @_;

  if ($use_ascii) {
    $ftp->ascii or die "Cannot set ascii mode: $!";
  } else {
    $ftp->binary or die "Cannot set binary mode: $!";
  }
}

=pod
Provide an eye-catching way of showing when we engage in different activities in this script
=cut
sub notify_new_activity {
  my ($activity) = @_;

  say "==> $activity <==";
}
