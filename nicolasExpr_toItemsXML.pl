#!/usr/bin/perl -w

use strict;
use warnings;
use Getopt::Std;

# we want to use say instead of print
use feature ':5.12';

# need to tell it where to find the modules
use lib "/SAN_synbiomine/data/SYNBIO_data/user_perl_modules";

# Load module dependencies
use BlastSynbio qw/run_BLAST/;
use SynbioGene2Location qw/geneLocation/;
use SynbioRegionSearch qw/regionSearch/;

# Use IM items modules
use InterMine::Item::Document;
use InterMine::Model;

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

# usage - also returned by -h
my $usage = "usage: $0 [-d|-h] nicolas_expression_tab IM_model_file.xml

\t-d\tverbose mode - for debugging

\t-h\tthis usage

\n";

### command line options - debugging and help ###
my (%opts, $debug);

getopts('hd', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"d"} and $debug++;

# test we have input files
unless ( $ARGV[1] ) { die $usage };

# allocate 
my ($expr_file, $model_file) = @ARGV;

# We need a look-up file to convert synonym [old] symbols to  B. sub unique identifiers
# synonyms file was downloaded from bacilluscope: ids, symbols and synonyms extracted
my $synonyms_file = "/SAN_synbiomine/data/SYNBIO_data/promoters/Bsub/Bsub_synonyms/bsub_id_symbol_synonyms_May2014.txt";

# open up the synonyms file
open(SYN_FILE, "< $synonyms_file") || die "cannot open $synonyms_file: $!\n";

# process id, symbol, synonyms file
my %id2synonym; # hash lookup for our symbols/ synonyms

# process the synonyms file and make a hash map
# format is uniqueId\tsymbol\tsynonym1, synonym2, etc
while (<SYN_FILE>) {
  chomp;
  my ($identifier, $symbol, $syn_line) = split("\t", $_);
  $id2synonym{$symbol} = [$identifier] if $symbol; # use array ref as some symbols are not unique

  my @synonyms;
  if ($syn_line) {
    if ($syn_line =~ m/, /) {
      @synonyms = split(", ", $syn_line); # if we have synonyms, split to array
    } else {
      if ( exists $id2synonym{$syn_line} ) {
	say "DUPLICATE: $syn_line $identifier" if ($debug);
	push(@{ $id2synonym{$syn_line} }, $identifier);
      } else {
	$id2synonym{$syn_line} = [$identifier];
      }
    }
  }

  foreach my $synonym (@synonyms) {
    if ( exists $id2synonym{$synonym} ) {
      say "DUPLICATE: $synonym $identifier" if ($debug);
      push(@{ $id2synonym{$synonym} }, $identifier);
    } else {
      $id2synonym{$synonym} = [$identifier];
    }
  }
}
close SYN_FILE;

if ($debug) {
  foreach my $key (keys %id2synonym) {
    say $key, " : ", join("; ", @{ $id2synonym{$key} });
  }
}

open(EXP_FILE, "< $expr_file") || die "cannot open $expr_file: $!\n";

chomp (my @matrix = <EXP_FILE>);
close (EXP_FILE);
#my $info = shift(@matrix);
my $headers = shift(@matrix); # extract headers

# splite headers and assign each to a variable
my ($id_h, $strand_h, $posV3_h, $posV3min_h, $posV3max_h, 
  + $multdbtbs_h, $comp_h, $sig_h, $pcomp_h, $psig_h, 
  + $xcortree_h, $SigmaFactorBS_h, $chipUnb_h, $chipMnb_h, 
  + $clcortreeUC_h, $clcortreeUB_h, $clcortreeUA_h, $VarExp_h, 
  + $VarExpPropUnexpl_h, $beginTU_h, $endTUshort_h, $endTUlong_h, 
  + $listShort_h, $listLong_h)  = split("\t", $headers);

# hard code parameters needed for data set/ source
my $taxon_id = "224308";
my $title = "Regulatory Features - The condition-dependent transcriptome of Bacillus subtilis 168";
my $pmid = "22383849";
my $accession = "GSE27219";
my $seq_length = 101;

my $chromosome = "NC_000964.3";
my $work_dir = "/SAN_synbiomine/data/SYNBIO_data/BLAST/Bsub168"; # our blast database

# set up the model
my $model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(model => $model);

# organism item
my $org_item = make_item(
    Organism => (
        taxonId => $taxon_id,
    )
);

# data_source_item
my $data_source_item = make_item(
    DataSource => (
        name => $title,
    ),
);

# publication_item
my $publication_item = make_item(
    Publication => (
        pubMedId => $pmid,
    ),
);

# promoter evidence code item
my $promoter_evidenceCode_item = &make_item(
    PromoterEvidenceCode => (
	name => "Promoters generated from around the start of detected transcriptional up-shifts - 101 bp spanning -60 bp to +40 bp",
    ),
);

# promoter_evidence_item
# promoter_evidence has a collection of evidence codes and publications
my $promoter_evidence_item = &make_item(
    PromoterEvidence => (
	evidenceCodes => [ $promoter_evidenceCode_item ],
	publications => [ $publication_item ],
    ),
);

# operon_evidenceCode_item
my $operon_evidenceCode_item = &make_item(
    OperonEvidenceCode => (
	name => "Based on Transcriptional Units (TUs) predicted from RNA hybridisation to 22bp resolution tiled microarrays",
    ),
);

# operon_evidence_item
# operon_evidence has a collection of evidence codes and publications
my $operon_evidence_item = &make_item(
    OperonEvidence => (
	evidenceCodes => [ $operon_evidenceCode_item ],
	publications => [ $publication_item ],
    ),
);

# promoter_data_set_item
my $promoter_data_set_item = make_item(
    DataSet => (
        name => "Promoters ($accession) for taxon id: $taxon_id",
	publication => $publication_item,
	dataSource => $data_source_item,
    ),
);

# operon_data_set_item
my $operon_data_set_item = make_item(
    DataSet => (
        name => "Operons ($accession) for taxon id: $taxon_id",
	publication => $publication_item,
	dataSource => $data_source_item,
    ),
);

# chromosome_item
my $chromosome_item = make_item(
    Chromosome => (
        primaryIdentifier => $chromosome,
    ),
);

# set up some hashes for tracking ids and items
my %seen_genes; # store genes that have been resolved to unique identifiers
my %seen_gene_items; # track processed gene items
my %seen_pred_sigma_items; # track processed predicted sigma items
my %seen_sigma_BF_items; # track processed sigma binding factor items
my %seen_operon_ids; # track processed operon ids
my %seen_operon_items; # track processed operon items

# loop through the data table rows and split out the values to variables
for my $entry (@matrix) {
#  chomp $entry;
  my ($id, $strand, $posV3, $posV3min, $posV3max, $multdbtbs, 
  + $comp, $sig, $pcomp, $psig, $xcortree, $SigmaFactorBS, $chipUnb, 
  + $chipMnb, $clcortreeUC, $clcortreeUB, $clcortreeUA, $VarExp, 
  + $VarExpPropUnexpl, $beginTU, $endTUshort, $endTUlong, $listShort, $listLong) = split("\t", $entry);

  $id = uc($id); # lowercase the entries

# BLAST seqs and process blast results - uses SynbioBlast.pm
  my ($regionRef);

# if we have a sigma binding site - we can balst the sequence to get the co-ords
  if ($SigmaFactorBS) {
    my $query = ">$id\n$SigmaFactorBS";
    $regionRef = &run_BLAST($query, $seq_length, $work_dir, $debug);
  }

# if we have blast results [$regionRef] we have a region
  my @prom_regions = @{ $regionRef } if ($regionRef);

# If we have a region - check that it has a unique location
  my $region;
  if ( scalar(@prom_regions) > 1) {
    warn "Sequence is not unique: $SigmaFactorBS\n"; # look for ambiguity
    next;
  } else {
    $region = $prom_regions[0]; # phew - we're unique, so grab the first element
  }

# turn the region string back into its sub-parts - 
# seems a bit clunky but makes it easier to send around...
  $region =~ m/(.+)\:(.+)\.\.(.+) (.+)/; 
  my ($chr, $start_found, $end_found, $strand_found) = ($1, $2, $3, $4) if ($region);

  if ($start_found) {

# process predicted Sigma Factors and split any that have multi-assignments
# e.g. SigABC
    my $pred_sig_factor = ($sig !~ m/Sig-/) ? $sig : undef;

    my ($prefix, $chars, @chars, @pred_sig_factors);
    if ($pred_sig_factor) {
      if ($pred_sig_factor =~ /^(Sig)([A-Z]+)/) { 
# split multipart identifier eg SigABC into Sig ABC
	$prefix = $1;
	$chars = $2;
	@chars = split(//, $chars); # split ABC part
	@pred_sig_factors = map { "Sig$_" } @chars; # add 'Sig' prefix to each eg. SigA
      } else {
	push (@pred_sig_factors, $pred_sig_factor); # if it's not multipart, add it to our array
      } 
    }

    my @operon = split(", ", $listShort); # get the operon genes from $listShort 
    my @operon_symbols = grep (!/^S\d/ && !/^NA/, @operon); # exclude the unvarified S[n] and those with symbol (NA)
    my $first_gene_id = $operon_symbols[0] if (@operon_symbols); # get the first gene

    say "Operon symbols - pre: ", join("-", @operon_symbols) if ($debug);
  
    next unless $first_gene_id; # if we don't have a gene we're not interested 
    say "Working on symbol: $first_gene_id" if ($debug);

    my $geneDBidentifier = &resolver($first_gene_id, $region); # try to get a unique gene ID
    next unless ($geneDBidentifier); # skip if we can't get a unique ID

  # we don't have promoter IDs so we'll form a unique one from the first gene etc.
    my $promoter_id = $id . "_" . $first_gene_id . "_" . $geneDBidentifier . "_" . $taxon_id;

    say "Operon symbols - post: ", join("-", @operon_symbols) if ($debug);

  ############################################
  # Set info for gene - first, check if we've seen it before
    my $gene_item = &make_gene_item($geneDBidentifier);

# resolve symbols and process predicted sigma factors
# Predictions are based on the expression clusters that they're assigned to
    my ($sigmaDBidentifier, $pred_sig_item, @pred_sig_items);
    for my $factor (@pred_sig_factors) {
      my $factor_id = lcfirst($factor);
      $sigmaDBidentifier = &resolver($factor_id, undef); # get the unique gene ID
      next unless ($sigmaDBidentifier); # skip if we don't find one
      
      # make a gene object for the sigmafactor
      my $pred_sig_gene_item = &make_gene_item($sigmaDBidentifier) if ($sigmaDBidentifier);
      say "PredSig: $sigmaDBidentifier has $pred_sig_gene_item with $psig" if  ($debug);

# check whether we've made a SF item
      if (exists $seen_pred_sigma_items{$sigmaDBidentifier}) {
	$pred_sig_item = $seen_pred_sigma_items{$sigmaDBidentifier}; # if yes, assign it
	
      } else {
# if no, make the predicted sigma factor items
	$pred_sig_item = make_item(
	  PredictedSigmaFactor => (
	    primaryIdentifier => $pred_sig_gene_item,
	    probability => $psig,
	  ),
	);
	$seen_pred_sigma_items{$sigmaDBidentifier} = $pred_sig_item; # add it to the tracker
      }
      push (@pred_sig_items, $pred_sig_item); # array of predicted sigma factor items - start a collection

    }

# process predicted Sigma Factor Binding sites and split any that have multi-assignments
# These SF predictions are based on 'known' binding sequences in the promoter
    my $sig_BF = ($multdbtbs !~ m/-/) ? $multdbtbs : undef;

    my (@sig_BFs, $sigmaBF_DBidentifier, $sigBF_gene_item, $sig_BF_item, @sig_BF_items);
    if ($sig_BF) {
      if ($sig_BF =~ m/,/) {
	@sig_BFs = split(/,/, $sig_BF);
      } else {
	push (@sig_BFs, $sig_BF);
      }

      for my $b_factor (@sig_BFs) {
	my $b_factor_id = lcfirst($b_factor);
	$sigmaBF_DBidentifier = &resolver($b_factor_id, undef);
	next unless ($sigmaBF_DBidentifier);

	my $sigBF_gene_item = &make_gene_item($sigmaBF_DBidentifier) if ($sigmaBF_DBidentifier);
	say "SigBF: $sigmaBF_DBidentifier has $sigBF_gene_item" if ($debug);

	if (exists $seen_sigma_BF_items{$sigmaBF_DBidentifier}) {
	  $sig_BF_item = $seen_sigma_BF_items{$sigmaBF_DBidentifier};
	  
	} else {
  # make predicted sigma binding factor items
	  $sig_BF_item = &make_item(
	    SigmaBindingFactor => (
	      primaryIdentifier => $sigBF_gene_item,
	    ),
	  );
	  $seen_sigma_BF_items{$sigmaBF_DBidentifier} = $sig_BF_item;
	}
	push (@sig_BF_items, $sig_BF_item); # array of sigma bf items - start a collection
      }
    }


  ############################################
  # Set info for sigma binding factor sequence 
    my $seq_item = make_item(
	Sequence => (
	    'length' => $seq_length,
	    residues => $SigmaFactorBS,
	),
    );

# and location
    my $location_item = make_item(
	Location => (
	    start => $start_found,
	    end => $end_found,
	    strand => $strand_found,
	    dataSets => [$promoter_data_set_item],
	),
    );

# start to put together the promoter item
   my $promoter_item = make_item(
       Promoter => (
	  primaryIdentifier => $promoter_id,
	  gene => $seen_gene_items{$geneDBidentifier},
	  predictedCluster => $comp,
	  clusterProbability => $pcomp,
	  chromosome => $chromosome_item,
	  chromosomeLocation => $location_item,
	  sequence => $seq_item,
	  evidence => [$promoter_evidence_item],
	  dataSets => [$promoter_data_set_item],
       ),
   );

# verbose output for debugging
  if ($debug) {
    say "Promoter:
	  primaryIdentifier: $promoter_id,
	  gene: $seen_gene_items{$geneDBidentifier},
	  predictedCluster: $comp,
	  clusterProbability: $pcomp,
	  chromosome: $chromosome_item,
	  chromosomeLocation: $location_item,
	  sequence: $seq_item,
	  evidence:$promoter_evidence_item,
	  dataSets: [$promoter_data_set_item]"
  }

# process operons
  my $operon_item = &make_operon_items(\@operon_symbols);
  say "Operon item for ", join("-", @operon_symbols), " is $operon_item" if ($debug);

# add our collections and references to the promoter item
  $promoter_item->set( predictedSigmaFactors => \@pred_sig_items ) if @pred_sig_items;
  $promoter_item->set( sigmaBindingFactors => \@sig_BF_items ) if @sig_BF_items;
  $promoter_item->set( operon => $operon_item );

############################################
###  Add completed promoter item collection to items for genes, tfac etc
  push( @{ $seen_gene_items{$geneDBidentifier}->{'promoters'} }, $promoter_item ) if ($geneDBidentifier);
  push( @{ $seen_pred_sigma_items{$sigmaDBidentifier}->{'promoters'} }, $promoter_item ) if ($sigmaDBidentifier);
  push( @{ $seen_sigma_BF_items{$sigmaBF_DBidentifier}->{'promoters'} }, $promoter_item ) if ($sigmaBF_DBidentifier);
  push( @{ $operon_item->{'promoters'} }, $promoter_item );
############################################

 }
}

$doc->close(); # writes the xml
exit(0);

####### MAIN SUBS #######
# resolver calls gene_lookup and returns a unique id, if known
sub resolver {
  my ($symbol, $region) = @_;
  my $gene2check = lcfirst($symbol);

  my $geneLookupRef = &gene_lookup($gene2check, $region);
  my @geneDBids = @{ $geneLookupRef } if ($geneLookupRef);

  my $geneDBidentifier;
  if ($geneLookupRef) {
    for my $identifier (@geneDBids) {
      say "Success: $gene2check resolved to $identifier" if ($debug);
      $geneDBidentifier = $identifier;
      $seen_genes{$gene2check} = $identifier unless (exists $seen_genes{$gene2check});
    }
  } else {
    say "Fail: Nothing returned from gene lookup with: $gene2check" if ($debug);
    return;
  }
  
  return $geneDBidentifier;

}

# If we have a location, use it to get the nearest gene(s)
# if not, use &synbiomine_genes to call SynBioMine's ID resolver to get the ID
sub gene_lookup {

  my ($gene_symbol, $region) = @_;

  my ($synbioRef, @identifiers);
# step 1. Have we seen the gene before? Yes - return that ID
  if ( exists $seen_genes{$gene_symbol} ) {
    say "Great! Already seen $gene_symbol. Reusing resolved ID..." if ($debug);
    push (@identifiers, $seen_genes{$gene_symbol});
    $synbioRef = \@identifiers;
    return $synbioRef;
  }

# process the region and extend co-ords by +/- 200 bp
  my ($chromosome, $start, $end, $strand, $extend_coord, $extend_region);

  if ($region) {
    $region =~ m/(.+)\:(.+)\.\.(.+) (.+)/; 
    ($chromosome, $start, $end, $strand) = ($1, $2, $3, $4);

    if ($strand =~ m/-/) {
      $extend_coord = ($start - 200);
      $extend_region = "$chromosome:$extend_coord..$end";
    } else {
      $extend_coord = ($end + 200);
      $extend_region = "$chromosome:$start..$extend_coord";
    }
  }  

# step 2. If not seen before, check if it's in the synonyms hash map
  if ( exists $id2synonym{$gene_symbol} ) {
    if (scalar( @{ $id2synonym{$gene_symbol} } > 1) ) {

# yes? if it's not unique, use the promoter location to get the gene ID from SynBioMine
      say "$gene_symbol is not unique: ", join("; ", @{ $id2synonym{$gene_symbol} }), "\n" if ($debug);

      if ($region) {
	say "Checking region ($extend_region) against SynBioMine..." if ($debug);

# call a module to query synbiomine regionSearch for gene id
	my ($org_short, $geneRef) = regionSearch($extend_region);
	my @genes_synbio = @$geneRef;

# returned results symbol and unique ID
	foreach my $synbio_gene (@genes_synbio) {
	  my $symbol = $synbio_gene->[0];
	  my $identifier = $synbio_gene->[1];
	  push (@identifiers, $identifier); # make a list of IDs
	  say "Found: $gene_symbol matches S: $symbol\tID: $identifier" if ($debug);
	}

      } else {
	say "No region - searching SynBioMine by ID..." if ($debug);
# step 3. If there's no region, use symbol and org name to look-up gene in SynBioMine
	my $geneRef = $id2synonym{$gene_symbol};
	$synbioRef = &synbiomine_genes($gene_symbol, $geneRef);
      }

    } else {
      say "Match: $gene_symbol matches: ", $id2synonym{$gene_symbol}->[0] if ($debug);
      my $match = $id2synonym{$gene_symbol}->[0];
      push (@identifiers, $match);
    }
  } else {
# if we can't find the ID in the Hashmap - look it up in SynBioMine
    say "Can't find $gene_symbol in lookup. Checking SynBioMine..." if ($debug);
    my $geneRef = [ $gene_symbol ];
    $synbioRef = &synbiomine_genes($gene_symbol, $geneRef);
  }

  $synbioRef = \@identifiers if (@identifiers);
  return $synbioRef;

}

# If we still don't have an ID, try SynBioMine's ID resolver to get the ID?
sub synbiomine_genes {

  my ($symbol2check, $gene2check) = @_;
  my $org_short = "B. subtilis subsp. subtilis str. 168";

  my @identifiers;
  foreach my $id ( @{ $gene2check} ) {

    my ($geneRef) = geneLocation($org_short, $id);
    my @gene_lookups = @$geneRef;

    if (scalar(@gene_lookups) > 1 ) {
      say "Houston, we have an ambiguity problem: $id" if ($debug);
    } else {
      my $identifier = $gene_lookups[0]->[0];
      my $symbol = $gene_lookups[0]->[1];

# check to see if the symbol returned matches the symbol we sent
      if ( ($symbol) && ($symbol eq $symbol2check) ) {
	say "Symbols match: $symbol eq $symbol2check - resolving to $identifier" if ($debug);
	push (@identifiers, $identifier); # if yes, add it to the ID list
	return \@identifiers;
      } 
      elsif ( ($symbol) && ($symbol ne $symbol2check) ) {
	say "Symbols don't match: $symbol eq $symbol2check - can't resolve $identifier" if ($debug);
      }
      else {
	say "$id not found in synbiomine!" if ($debug);
      }
    }
  }

# if we have ID matches, return them - otherwise, return
  if (@identifiers) {
    \@identifiers;
  } else { return; }

}

######## helper subroutines:
# if the gene is in out item tracker return it
# otherwise, make a new gene item, add it to the tracker and return it
sub make_gene_item {
  my $id = shift;

  my $gene_item;
  if (exists $seen_gene_items{$id}) {
    $gene_item = $seen_gene_items{$id};
  } else {
    $gene_item = make_item(
	Gene => (
	    primaryIdentifier => $id,
	),
    );

    $seen_gene_items{$id} = $gene_item;
  }
  return $gene_item;
}

# make items for the operons we're processing
sub make_operon_items {
  
  my $operonRef = shift;

  my $operon_code = join("-", @{ $operonRef } );
  my $operon_uid = $operon_code  . "_Nicolas2012_" . $taxon_id; # unique operon ID
  say "OperonUID: ", $operon_uid if ($debug);

  my ($operon_item, @operon_gene_items);
  if ( exists $seen_operon_items{$operon_uid} ) {
    $operon_item = $seen_operon_items{$operon_uid}; # if we've already seen this one, assign it
  } else {
      # if it's new, set info for Operon
    $operon_item = &make_item(
      Operon => (
	primaryIdentifier => $operon_uid,
	evidence => [ $operon_evidence_item ],
	dataSets => [$operon_data_set_item],
      ),
    );

# resolve the symbols and get the gene objects for the operon genes
    for my $gene_id ( @{ $operonRef } ) {
      my $geneDBidentifier = &resolver($gene_id, undef);
      next unless ($geneDBidentifier);
      say "OperonGene: $gene_id is $geneDBidentifier" if ($debug);
      my $gene_item = &make_gene_item($geneDBidentifier);
      push (@{ $operon_item->{'genes'} }, $gene_item); # add gene collection to the operon

    }

    $seen_operon_items{$operon_uid} = $operon_item; # add the new operon item to our tracker
  }

  return $operon_item; # does what it says on the tin
}

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);
    if ($item->valid_field('organism')) {
        $item->set(organism => $org_item);
    }
    return $item;
}
