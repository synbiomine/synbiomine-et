#!/usr/bin/perl

use strict;
use warnings;
use File::Spec::Functions;
use File::Tee qw(tee);
use Getopt::Std;
use Net::FTP;
use Time::localtime;

use feature ':5.12';

my $selected_genomes_fn = "synbiomine_selected_assembly_summary_refseq.txt";

my $usage = "Usage: selectGenomes.pl [-hv] [-p <pre_selected_genomes_path>] <dataset_path>

Downloads assembly summaries from NCBI and selects genomes according to hard-coded criteria.
Writes the selected summaries to <dataset_path>/genbank/$selected_genomes_fn

options:
\t-h\tthis usage
\t-p\tpath to a file containing pre-selected genomes by NCBI assembly reference.  Normally we would expect to use etc/pre_selected_genomes.txt in this repository
\t-v\tmore verbose logging

";

my (%opts, $verbose, $load_preselected_assemblies, $preselected_assemblies_path);

getopts('hp:v', \%opts);
defined $opts{"h"} and die $usage;


if (defined $opts{"p"}) {
  $load_preselected_assemblies = 1;
  $preselected_assemblies_path = $opts{"p"};
}
defined $opts{"v"} and $verbose = 1;

# date settings - used to make a new working folder
my $tm = localtime;
my ($DAY, $MONTH, $YEAR) = ($tm->mday, ($tm->mon) + 1, ($tm->year) + 1900);

@ARGV > 0 or die $usage;

my $genbank_dir = "$ARGV[0]/genbank";

# At this point we have established that the dataset exists and want to start logging our activity
tee STDOUT, '>>', "$genbank_dir/logs/selectGenomes.log";

my $contact = 'justincc@intermine.org'; # Please set your email address here to help us debug in case of problems.

# Global FTP params
$ENV{FTP_PASSIVE} = 1;
my $timeout      = 600;     # seconds, default is 120
#my $retries      = 5;
my $username = 'anonymous'; # allow anonymous FTPO with email addr as pwd
my $password = 'justincc@intermine.org'; # required

notify_new_activity("Downloading NCBI assembly summary");

# set ftp address for ncbi
my $hostname = 'ftp.ncbi.nlm.nih.gov';

# Hardcode the directory and filename we want to get
my $home = '/genomes/ASSEMBLY_REPORTS';
my $file = 'assembly_summary_refseq.txt'; # this is where we get the look-up file that maps assembly ID to organism

my $ncbi_ftp = Net::FTP->new($hostname, BlockSize => 20480, Timeout => $timeout);

$ncbi_ftp->login($username, $password) or die "Cannot login ", $ncbi_ftp->message;
$ncbi_ftp->cwd($home) or die "Cannot change working directory ", $ncbi_ftp->message;

my $assem_ref = &fetch_filtered_data($ncbi_ftp, $file, catdir($genbank_dir, $file));

$ncbi_ftp->quit;

my @assem = @{ $assem_ref };

notify_new_activity("Selecting assemblies");

my %preselectedAssemblies = ();

if ($load_preselected_assemblies) {
  open PRESELECTED, $preselected_assemblies_path or die "Could not open $preselected_assemblies_path for reading: $!";

  while (<PRESELECTED>) {
    /^#/ and next;
    chomp;
    $preselectedAssemblies{$_} = 1;
  }

  # @preselectedAssemblies = <PRESELECTED>;
  close PRESELECTED;

  say "Loaded " . keys(%preselectedAssemblies) . " pre-selected assemblies from $preselected_assemblies_path";
}

my %selectedAssem = ();

for (@assem) {
  chomp;

  my($assembly_id, $bioproject, $biosample, $wgs_master, $refseq_category, $taxid,
    $species_taxid, $organism_name, $infraspecific_name, $isolate, $version_status,
    $assembly_level, $release_type, $genome_rep, $seq_rel_date, $asm_name,
    $submitter, $gbrs_paired_asm, $paired_asm_comp) = split("\t", $_);

  say "Examining $taxid => $assembly_id, $organism_name" if ($verbose);

  if (exists($preselectedAssemblies{$assembly_id})) {
    say "Adding $taxid => $assembly_id as preselected";
    $selectedAssem{$taxid} = $_;
    next;
  }

# We're only interested in reference or representative genomes - complete and probably have refseq annotations
# they used to use hyphen, now they use space so check for both in case they change back
  if (not ($refseq_category && $refseq_category =~ /-genome| genome/)) {
    say "Ignoring non-genome category $refseq_category" if ($verbose);
    next;
  }

# We want the chromosome data
  # if (not $assembly_level =~ /Chromosome/) {
  if (not $assembly_level =~ /Chromosome|Complete Genome/) {
    say "Ignoring non-chromosome assembly level $assembly_level" if ($verbose);
    next;
  }

  # next unless (($refseq_category) && ($refseq_category =~ /-genome| genome/)); 

  # There's a strange Bacillus species that has [] around its name!
  # [Bacillus] selenitireducens MLS10
  $organism_name =~ s/\[/_/;
  $organism_name =~ s/\]//;

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
  if ( exists $selectedAssem{$taxid} ) {
  # For B. subtilis 168 we want the representative genome - the reference genome has odd IDs
    if ( ($taxid eq '224308') and ($refseq_category =~ /reference-genome/) ) {
      say "Specifically ignoring reference genome for this organism" if ($verbose);
      next;
    }
    elsif ($refseq_category =~ /representative-genome/) {
      say "Ignoring representative genome as we already have an assembly for this organism" if ($verbose);
      next;
    }

    say "Replacing assembly $selectedAssem{$taxid}[1] with later candidate $assembly_vers" if ($verbose);
  }

  $selectedAssem{$taxid} = $_;
}

# Do this in sorted order
for my $key (sort {$a <=> $b} keys %selectedAssem) {

  # XXX: Yes, this is hellish messy
  my($assembly_id, $bioproject, $biosample, $wgs_master, $refseq_category, $taxid,
    $species_taxid, $organism_name, $infraspecific_name, $isolate, $version_status,
    $assembly_level, $release_type, $genome_rep, $seq_rel_date, $asm_name,
    $submitter, $gbrs_paired_asm, $paired_asm_comp) = split("\t", $selectedAssem{$key});

  say "Selected $key => $assembly_id, $refseq_category, $organism_name";
}

say "Selected " . keys(%selectedAssem) . " assemblies";

my $selected_genomes_path = catdir($genbank_dir, $selected_genomes_fn);

open SELECTED_ASSEM, ">$selected_genomes_path" or die "Could not write to $selected_genomes_path: $!\n";

foreach my $assem (values(%selectedAssem)) {
  say SELECTED_ASSEM $assem;
}

close SELECTED_ASSEM;

##############################
######## SUBROUTINES #########
##############################

=pod
Return FTP data where lines have t omatch Bacillus|Escherichia|Geobacillus
=cut
sub fetch_filtered_data {

  my ($ftp, $src, $dest) = @_;

  #my @dir_list = grep /_uid/, $ftp->ls();

  # We're using a filehandle on the basis that it is more memory efficient as we can discard each
  # retrieved line after processing instead of slurping in the whole file at once
  #my $handle = $ftp->retr($file) or die "get failed ", $ftp->message;
  $ftp->get($src, $dest) or die "Failed to get $src for $dest: $ftp->message";

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
Provide an eye-catching way of showing when we engage in different activities in this script
=cut
sub notify_new_activity {
  my ($activity) = @_;

  say "~~~ $activity ~~~";
}
