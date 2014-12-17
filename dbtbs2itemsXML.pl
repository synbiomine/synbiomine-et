#!/usr/bin/perl

use strict;
use warnings;
use XML::Twig;
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

my $usage = "Usage:dbtbs2itemsXML.pl DBTBS.xml InterMine_model OUT_FILE 

Synopsis: consumes a static file dbtbs.xml containing transcriptional regulatory
information for Bacillus subtilis 168. Output creates items XML linking genes
to regulatory info e.g. promoters, transcription factors, sigma factors,
operons and terminators. 

\tOUT_FILE : just to capture verbose output for testing

We still need to redirect output to file e.g:\t> dbtbd_items.xml_file

Optionally, capture errors & warning:\t2> err

Note: These data are needed by Bacillus RegNet for orthologous regulation prediction
across species/ strains.

";

### command line options ###
my (%opts, $debug);

getopts('hd', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"d"} and $debug++;

unless ( $ARGV[2] ) { die $usage };

# specify and open query file (format: )
my ($xml_file, $model_file, $out_file) = @ARGV;

### Keep a track of processed identifiers and items
my %seen_tfac;
my %seen_genes; # store genes that have been resolved to unique identifiers
my %seen_refs; # store of refs that have already been processed
my %seen_promoters; # store promoter ids so that we can create unique identifiers
my %seen_gene_items; # track processed gene items
my %seen_ref_items; # track processed reference items
my %seen_tfac_items; # track processed tfac items
my %seen_sigma_items; # track processed tfac items
my %evidenceCode_items;
my %seen_publication_items;

# We need a look-up file to convert synonym [old] symbols to  B. sub unique identifiers
# synonyms file was downloaded from bacilluscope: ids, symbols and synonyms extracted
my $synonyms_file = "/SAN_synbiomine/data/SYNBIO_data/promoters/Bsub/Bsub_synonyms/bsub_id_symbol_synonyms_May2014.txt";

# open up the synonyms file
open(SYN_FILE, "< $synonyms_file") || die "cannot open $synonyms_file: $!\n";

# process id, symbol, synonyms file
my %id2synonym; # hash lookup for symbols/ synonyms

# process the synonyms file and make a hash map
# format is uniqueId\tsymbol\tsynonym1, synonym2, etc
while (<SYN_FILE>) {
  chomp;
  my ($identifier, $symbol, $syn_line) = split("\t", $_);
  $id2synonym{$symbol} = [$identifier] if $symbol; # use array ref as some symbols are not unique

  my @synonyms;
  if ($syn_line) {
    if ($syn_line =~ m/, /) {
      @synonyms = split(", ", $syn_line);
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

### show contents of look-up hash for debugging
if ($debug) {
  foreach my $key (keys %id2synonym) {
    say $key, " : ", join("; ", @{ $id2synonym{$key} });
  }
}

# set up our oufile to check everything's working
open OUT_FILE, ">$out_file" or die $!; 

# set a few global values that we'll need
my $taxon_id = "224308";
my $title = "DBTBS - Regulatory features for Bacillus subtilis 168";
my $url = "http://dbtbs.hgc.jp";
my $chromosome = "NC_000964.3";

my $work_dir = "/SAN_synbiomine/data/SYNBIO_data/BLAST/Bsub168"; # our blast database

# instantiate the model
my $model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(model => $model);

# make organism items
my $org_item = make_item(
    Organism => (
        taxonId => $taxon_id,
    )
);

# make DataSource items
my $data_source_item = make_item(
    DataSource => (
        name => $title,
	url => $url,
    ),
);

# make Promoter DataSet items
my $promoter_data_set_item = make_item(
    DataSet => (
        name => "DBTBS Promoters for taxon id: $taxon_id",
	dataSource => $data_source_item,
    ),
);

# make Operon DataSet items
my $operon_data_set_item = make_item(
    DataSet => (
        name => "DBTBS Operons for taxon id: $taxon_id",
	dataSource => $data_source_item,
    ),
);

# make Chromosome items
my $chromosome_item = make_item(
    Chromosome => (
        primaryIdentifier => $chromosome,
    ),
);

# Use Twig parser to process XML - via Twig handlers
my $twig_tf = XML::Twig->new(
    twig_handlers => {
        'dbtbs/tfac' => \&process_tfac,
    },
);

$twig_tf->parsefile( "$xml_file" );

# Use Twig parser to process XML - via Twig handlers
my $twig = XML::Twig->new(
    twig_handlers => {
        'dbtbs/promoter' => \&process_promoters,
        'dbtbs/operon' => \&process_operon,
    },
);

$twig->parsefile( "$xml_file" ); # call to parse the XML file


$doc->close(); # writes the xml
exit(0);

# 
close OUT_FILE;

### Sub routines for each of the Twig handlers

### process the promoter entries
sub process_promoters {
  my ($twig, $entry) = @_;

  say "PROMOTER: \t" if ($debug);
  
  my $gene_DBTBS = ( $entry->first_child( 'gene' ) ) ? $entry->first_child( 'gene' )->text : undef;
  my $tfac = ( $entry->first_child( 'tfac' ) ) ? $entry->first_child( 'tfac' )->text : undef;
  my $sigma = ( $entry->first_child( 'sigma' ) ) ? $entry->first_child( 'sigma' )->text : undef;
  my $id = ( $entry->first_child( 'name' ) ) ? $entry->first_child( 'name' )->text : undef;
  my $regulation = ( $entry->first_child( 'regulation' ) ) ? $entry->first_child( 'regulation' )->text : undef;
  my $prom_seq = ( $entry->first_child( 'sequence' ) ) ? $entry->first_child( 'sequence' )->text : undef;
  my $location = ( $entry->first_child( 'location' ) ) ? $entry->first_child( 'location' )->text : undef;

  my @refs = $entry->children( 'reference' );

  say OUT_FILE "Looking for TFAC: $tfac ..." if ( ($debug) && ($tfac) );

  my $tfac_family;
  if ( ($tfac) && (exists $seen_tfac{$tfac}) ) {
    $tfac_family = $seen_tfac{$tfac};
    say OUT_FILE "FOUND TFAC: $tfac with $tfac_family" if $debug;
  }

  $id =~ s/,/_/g;
  my $synonym = $id if ($id);
  
# the promoter sequence is in a strange format - highlighting binding site
# Need to strip-out extra chars so we can Blast the seq

  $prom_seq =~ tr|[A-Z]|[a-z]|;
  $prom_seq =~ s|\{(.+?)\}|uc($1)|eg;
  $prom_seq =~ s|\/(.+)\/|uc($1)|eg;

  my $query = ">$gene_DBTBS\n$prom_seq";
  my $seq_length = &seq_length( $prom_seq ) if ($prom_seq);

# BLAST promoter seq against B. sub genome to get location
  my $region_ref = &run_BLAST( $query, $seq_length, $work_dir, $debug ) if ($prom_seq);

  my @prom_regions = @{ $region_ref } if ($region_ref);

# If we have a region - check that it has a unique location
  my $region;
  if ( scalar(@prom_regions) > 1) {
    warn "Sequence is not unique: $prom_seq\n";
    next;
  } else {
    $region = $prom_regions[0];
  }

# turn the region string back into its sub-parts - seems a bit clunky but hey...
  $region =~ m/(.+)\:(.+)\.\.(.+) (.+)/; 
  my ($chr, $start, $end, $strand) = ($1, $2, $3, $4) if ($region);

### If we have a unique region, make a location and sequence items 
  my ($location_item, $seq_item);
  if ($region) {
    $location_item = &make_item(
	Location => (
	  start => "$start",
	  end => "$end",
	  strand => "$strand",
	  dataSets => [$promoter_data_set_item],
	),
    );

############################################
# If we have sequence, set info for sequence item
    $seq_item = &make_item(
      Sequence => (
	'length' => $seq_length,
	residues => $prom_seq,
      ),
    );
  }

  my ($geneDBidentifier, $tfacDBidentifier, $sigmaDBidentifier);
  $geneDBidentifier = &resolver($gene_DBTBS, $region);
  next unless ($geneDBidentifier); # skip if we can't get a unique ID

  ############################################
# Set info for gene - first, check if we've seen it before
  my $gene_item = &gene_item($geneDBidentifier);

  $tfacDBidentifier = &resolver($tfac, undef) if $tfac;
  $sigmaDBidentifier = &resolver($sigma, undef) if $sigma;

# generate a unique identifier for each promoter
  my $promoter_id = $gene_DBTBS . "_" . $geneDBidentifier . "_dbtbs_" . $taxon_id;
  $seen_promoters{$promoter_id}++;
  
  my $promoter_uid = $promoter_id . "_" . $seen_promoters{$promoter_id};

### Process the experimental evidence
  my $refsRef = &process_refs("PromoterEvidence", \@refs, undef);
  my @evidence = @{ $refsRef };

  say "UID: $promoter_uid" if ($debug);

  my $promoter_item = &make_item(
      Promoter => (
	  primaryIdentifier => $promoter_uid,
	  chromosome => $chromosome_item,
	  dataSets => [$promoter_data_set_item],
      ),
  );

  $promoter_item->set( synonym => $synonym ) if ($synonym);
  $promoter_item->set( evidence => $refsRef ) if ($refsRef);

  if ($location_item) {
    # Add sequence and location items to promoter if applicable
    $promoter_item->set( chromosomeLocation => $location_item );
    $promoter_item->set( sequence => $seq_item );
  }

### Start adding our gene objects - gene, tfac and sigma factor
### Promoter gene items ###
  if (exists $seen_gene_items{$geneDBidentifier}) {
    $promoter_item->set( gene => $seen_gene_items{$geneDBidentifier} );
  } else {
    $promoter_item->set( gene => $gene_item );
    $seen_gene_items{$geneDBidentifier} = $gene_item;
  }

### Transcription Factor items ###
  my $tfac_item;
  if ($tfacDBidentifier) {
    unless (exists $seen_tfac_items{$tfacDBidentifier}) {
  ############################################
  # Set gene info for sigma - first, check if we've seen it before

      my $tfac_gene_item = &gene_item($tfacDBidentifier);
      unless (exists $seen_gene_items{$tfacDBidentifier}) {
	$seen_gene_items{$tfacDBidentifier} = $tfac_gene_item;
      }

############################################
# Set info for Sigma Factor - first, check if we've seen it before
      $tfac_item = &make_item(
	TranscriptionFactor => (
	    primaryIdentifier => $tfac_gene_item,
	    regulation => $regulation,
	),
      );

      if ($tfac_family) {
	$tfac_item->set( tfFamily => $tfac_family );
      }

    }

    if (exists $seen_tfac_items{$tfacDBidentifier}) {
      $promoter_item->set( transcriptionFactor => $seen_tfac_items{$tfacDBidentifier} );
    } else {
      $promoter_item->set( transcriptionFactor => $tfac_item );
      $seen_tfac_items{$tfacDBidentifier} = $tfac_item;
    }
  }

############################################
### Sigma Factor Binding items ###

  my $sigma_item;
  if ($sigmaDBidentifier) {
    unless (exists $seen_sigma_items{$sigmaDBidentifier}) {
  ############################################
  # Set gene info for sigma - first, check if we've seen it before
    my $sigma_gene_item = &gene_item($sigmaDBidentifier);
      unless (exists $seen_gene_items{$sigmaDBidentifier}) {
	$seen_gene_items{$sigmaDBidentifier} = $sigma_gene_item;
      }

############################################
# Set info for Sigma Factor - first, check if we've seen it before
      $sigma_item = &make_item(
	  SigmaBindingFactor => (
	    primaryIdentifier => $sigma_gene_item,
	  ),
      );
    }

    if (exists $seen_sigma_items{$sigmaDBidentifier}) {
      $promoter_item->set( sigmaBindingFactors => [ $seen_sigma_items{$sigmaDBidentifier} ] );
    } else {
      $promoter_item->set( sigmaBindingFactors => [ $sigma_item ] );
      $seen_sigma_items{$sigmaDBidentifier} = $sigma_item;
    }
  }

############################################
###  Add completed promoter item to collection for genes, tfac etc
  push( @{ $seen_gene_items{$geneDBidentifier}->{'promoters'} }, $promoter_item ) if ($geneDBidentifier);
  push( @{ $seen_tfac_items{$tfacDBidentifier}->{'promoters'} }, $promoter_item ) if ($tfacDBidentifier);
  push( @{ $seen_sigma_items{$sigmaDBidentifier}->{'promoters'} }, $promoter_item ) if ($sigmaDBidentifier);

############################################

  if ($debug) {
    say OUT_FILE "\nPromoter UID: $promoter_uid";
    say OUT_FILE "	Synonym: $id" if ($id);
    say OUT_FILE "	Gene: $gene_DBTBS $geneDBidentifier";
    say OUT_FILE "	Sigma: $sigma $sigmaDBidentifier" if ($sigma);
    say OUT_FILE "	Sequence: $prom_seq" if ($prom_seq);
    say OUT_FILE "	SeqLen: $seq_length" if ($prom_seq);
    say OUT_FILE "	Region: $chr, $start, $end, $strand" if ($region);
    say OUT_FILE "	Location: $location" if ($location);
    say OUT_FILE "	Tfac: $tfac $tfacDBidentifier" if ($tfac);
    say OUT_FILE "	Reg: $regulation" if ($regulation);

    if (@evidence) {
      say OUT_FILE "	Evidence: ", join("; ", @evidence);
    }
  }

  $twig->purge();
}

### process the transcription factor entries
## don't need so all code commented
sub process_tfac {
  my ($twig, $entry) = @_;

# #  say OUT_FILE "TF: \t";

  my $gene_tfac = ( $entry->first_child( 'gene' ) ) ? $entry->first_child( 'gene' )->text : undef;
  my $tf_type = ( $entry->first_child( 'tf_type' ) ) ? $entry->first_child( 'tf_type' )->text : undef;

  say OUT_FILE "TFAC: processing $gene_tfac" if ($debug);
#  next unless $tf_type;
  say OUT_FILE "TFAC type: $tf_type" if ( ($debug) && ($tf_type) );

  $seen_tfac{$gene_tfac} = $tf_type if ($tf_type);
# #   my $domain = ( $entry->first_child( 'domain' ) ) ? $entry->first_child( 'domain' )->text : undef;
# #   my $tf_seq = ( $entry->first_child( 'sequence' ) ) ? $entry->first_child( 'sequence' )->text : undef;
# #   my $comment = ( $entry->first_child( 'comment' ) ) ? $entry->first_child( 'comment' )->text : undef;

# #   say OUT_FILE "$gene_tfac $tf_type $domain";
# #   say OUT_FILE $tf_seq;
# #   say OUT_FILE $comment;

  $twig->purge();
}

### process the operon entries
sub process_operon {
  my ($twig, $entry) = @_;

#  say OUT_FILE "\nOPERON: \t";

  my $id = ( $entry->first_child( 'name' ) ) ? $entry->first_child( 'name' )->text : undef;
  my $operon_uid = $id . "_" . "dbtbs_" . $taxon_id;

  ############################################
# Set info for Operon
  my $operon_item = &make_item(
      Operon => (
	primaryIdentifier => $operon_uid,
	synonym => $id,
	dataSets => [$operon_data_set_item],
      ),
  );

  my $gene_operon = ( $entry->first_child( 'genes' ) ) ? $entry->first_child( 'genes' )->text : undef;
  my @operon_genes = split(',', $gene_operon);

  my @operon_gene_items;
  foreach my $operon_gene (@operon_genes) {
    my $operon_geneDBid = &resolver($operon_gene, undef);
    next unless ($operon_geneDBid);
  ############################################
# Set info for gene - first, check if we've seen it before
    my $operon_gene_item = &gene_item($operon_geneDBid);
    push(@operon_gene_items, $operon_gene_item);
  }

  $operon_item->set( genes => \@operon_gene_items );

  if ($debug) {
    say OUT_FILE "\n
      Operon => (
      primaryIdentifier => $operon_uid
      synonym => $id";
    say OUT_FILE "	genes => ", join("; ", @operon_genes);
  }

  my $experiment = ( $entry->first_child( 'experiment' ) ) ? $entry->first_child( 'experiment' )->text : undef;
  my @experiments;
  if ($experiment) {
    if ($experiment =~ m/\; /) {
      @experiments = split("; ", $experiment)
    } else {
      push(@experiments, $experiment)
    }
  }

### Process the experimental evidence
  my @refs = $entry->children( 'reference' );
  
  my $refsRef;
  if ($experiment) {
    $refsRef = &process_refs("OperonEvidence", \@refs, \@experiments);
  } else {
    $refsRef = &process_refs("OperonEvidence", \@refs, undef);
  }
  
  my @evidence;
  if ($refsRef) {
    @evidence = @{ $refsRef };
    $operon_item->set( evidence => $refsRef );
  }

  if (@evidence) {
    say OUT_FILE "	OperonEvidence: ", join("; ", @evidence) if ($debug);
  }

  my $comment = ( $entry->first_child( 'comment' ) ) ? $entry->first_child( 'comment' )->text : undef;
  $operon_item->set( comment => $comment ) if ($comment);

### Process terminator info
  my ($term_seq, $energy);
  my @terminators = $entry->children( 'terminator' );

  my ($terminator_item, @terminator_items, %seen_terminators);
  if (@terminators) {
    for my $terminator (@terminators) {
      $term_seq = ( $terminator->first_child( 'stemloop' ) ) ? $terminator->first_child( 'stemloop' )->text : undef;
      $energy = ( $terminator->first_child( 'energy' ) ) ? $terminator->first_child( 'energy' )->text : undef;

      my $terminator_id = "Terminator" . "_" . $operon_uid;
      $seen_terminators{$terminator_id}++;
      my $terminator_uid = $terminator_id . "_" . $seen_terminators{$terminator_id};

      $terminator_item = &make_item(
	    BacterialTerminator => (
	      primaryIdentifier => $terminator_uid,
	      energy => $energy,
	      stemloop => $term_seq,
	      chromosome => $chromosome_item,
	      dataSets => [$operon_data_set_item],
	    ),
      );

      my $query_seq = $term_seq;
      $query_seq =~ s/\{.+?\}//g;
  #    say OUT_FILE "	TERMseq: ", $term_seq;

      my $term_query = ">$id\n$query_seq\n";
      my $seq_length = &seq_length( $query_seq ) if ($query_seq);

      say "Blasting Terminator: $id to find coordinates..." if ($debug);
      my $region_ref = &run_BLAST( $term_query, $seq_length, $work_dir, $debug ) if ($query_seq);
      my @term_regions = @{ $region_ref } if ($region_ref);

    # If we have a region - check that it has a unique location
      my $region;
      if ( scalar(@term_regions) > 1) {
	warn "Sequence is not unique: $query_seq\n";
	next;
      } else {
	$region = $term_regions[0];
      }

    # turn the region string back into its sub-parts - seems a bit clunky but hey...
      $region =~ m/(.+)\:(.+)\.\.(.+) (.+)/; 
      my ($chr, $start, $end, $strand) = ($1, $2, $3, $4) if ($region);

    ### If we have a unique region, make a location and sequence items 
      my ($location_item, $seq_item);
      if ($region) {
	$location_item = &make_item(
	    Location => (
	      start => $start,
	      end => $end,
	      strand => $strand,
	      dataSets => [$operon_data_set_item],
	    ),
	);

    ############################################
    # If we have sequence, set info for sequence item
      $seq_item = &make_item(
	Sequence => (
	  'length' => $seq_length,
	  residues => $query_seq,
	),
      );

	$terminator_item->set( chromosomeLocation => $location_item, );
	$terminator_item->set( sequence => $seq_item, );
      }
      $terminator_item->set( operon => $operon_item, );
      push(@terminator_items, $terminator_item);

      if ($debug) {
	say OUT_FILE "
	  primaryIdentifier => $terminator_uid,
	  energy => $energy,
	  stemloop => $term_seq,
	  Location =>
	    chromosome => $chromosome,
	    start => $start,
	    end => $end,
	    strand => $strand,
	    length => $seq_length,
	    residues => $query_seq";
      }
      
    }
    $operon_item->set( terminator => \@terminator_items );
  }

  $twig->purge();
}

### Whole bunch of other subroutines to save redundant code

# Takes literature references and turns them into 'Evidence' items
sub process_refs {
  my ($type, $arrRef, $experRef) = @_;

  my @refs = @{ $arrRef };

  my ($processed_ref, @processed_refs);

  #### PLAYED AROUND WITH THIS SECTION - inconsistencies in the dbtbs file
  # cause problems as promoters and operons handle references differently
  # Promoters: multiple evidence codes per publication
  # Operons: experiment is independent but multiple publications per evidence code

   foreach my $ref (@refs) {
    my $experiment = ( $ref->first_child( 'experiment' ) ) ? $ref->first_child( 'experiment' )->text : undef;
    my $pmid = ( $ref->first_child( 'pubmed' ) ) ? $ref->first_child( 'pubmed' )->text : undef;
    my $author = ( $ref->first_child( 'author' ) ) ? $ref->first_child( 'author' )->text : undef;
    my $year = ( $ref->first_child( 'year' ) ) ? $ref->first_child( 'year' )->text : undef;
    my $title = ( $ref->first_child( 'title' ) ) ? $ref->first_child( 'title' )->text : undef;
    my $genbank = ( $ref->first_child( 'genbank' ) ) ? $ref->first_child( 'genbank' )->text : undef;
    my $link = ( $ref->first_child( 'link' ) ) ? $ref->first_child( 'link' )->text : undef;

    next unless ($pmid || $title); # just track the publications we can model

    # Evidence 'type' is supplied to the subroutine and can be
    # either 'PromoterEvidence' or 'OperonEvidence'
    my $evidence_item = &make_item(
      $type => (
      ),
    );

    # For some reason, dbtbs models reference evidence differently for 
    # promoters vs. operons, so we need to define different rules
    my ($evidenceRefs, @evidence_codes, $evidenceCode_item);

    # First, we'll process evidence from promoters
    if ($experiment) {
      
      @evidence_codes = split(" ", $experiment); # split to get 2 letter codes
      $evidenceRefs = &evidence_lookup(\@evidence_codes); # looks up the codes to get descriptions
      # creates a collection of evidenceCode items
      $evidence_item->set( evidenceCodes => $evidenceRefs ) if ( $evidenceRefs );

    } elsif ($experRef) {
      # Now, we'll process experimental evidence from operons
      # check if we have a ref to an operon 'experiments' array

      my @operon_evidenceCode_items; # array to hold evidenceCode items

      # deref array ref and loop over our evidence strings
      for my $evidence ( @{ $experRef } )  {

	say "Processing Exper: $evidence" if ($debug);
	$evidence =~ s/Northern blot.+/Northern blotting/;
	$evidence =~ s/\)//;
	$evidence =~ s/\(//;
	next if ($evidence =~ / opposite /); # info about strands isn't really evidence.
	# Better described as a comment? Any, don't need it.

	# check hash to see whether we've already made an evidenceCode item for this exper
	# Difficult to follow so add a bunch of debug output code

	# If we can, we want to re-use any evidence code items. 
	# This said, might be a bit pointless as dbtbs file seems not to handle them consistently!
	if (exists $evidenceCode_items{$evidence}) {
	  say "Seen Exper before: $evidence" if ($debug);
	  my $evidenceCode_item = $evidenceCode_items{$evidence}; # if yes, use the stored evidenceCode item
	  push(@operon_evidenceCode_items, $evidenceCode_item); # add it to our evidenceCode item array
	} else {
	  # if no, make a new evidenceCode item
	  say "Haven't seen Exper before: $evidence. Making a new one" if ($debug);
	  $evidenceCode_item = &make_item(
	    OperonEvidenceCode => (
	      name => $evidence,
	    ),
	  );
	  say "Adding: $evidence to evidenceCode items array" if ($debug);
	  push(@operon_evidenceCode_items, $evidenceCode_item); # add it to our evidenceCode item array
	  $evidenceCode_items{$evidence} = $evidenceCode_item; # add new item to our evidenceCode item hash lookup
	}
      }
      say "Adding evidenceCode items array as collection to evidence item" if ($debug);
      $evidence_item->set( evidenceCodes => \@operon_evidenceCode_items ) if (@operon_evidenceCode_items);
    }

    $author =~ s/\&amp\;/and/g; # Some author fields look to have funny encodings
    $author =~ s/, et al\.//g; # get rid of the et al.

  
    # Now process the publications ato get publications items
    my ($publication_item, @publications_items);
    if ($pmid) {
      if (exists $seen_publication_items{$pmid} ) {
	$publication_item = $seen_publication_items{$pmid};
	push(@publications_items, $publication_item);
      } else {
	$publication_item = &make_item(
	  Publication => (
	    pubMedId => $pmid,
	  ),
	);
	push(@publications_items, $publication_item);
	$seen_publication_items{$pmid} = $publication_item;
      }
    } elsif ($title) {
      if (exists $seen_publication_items{$title} ) {
	$publication_item = $seen_publication_items{$title};
	push(@publications_items, $publication_item);
      } else {
	$publication_item = &make_item(
	  Publication => (
	    firstAuthor => $author,
	    title => $title,
	    year => $year,
	  ),
	);
	push(@publications_items, $publication_item);
	$seen_publication_items{$title} = $publication_item;
      }
    }

    $evidence_item->set( publications => \@publications_items, );
    push(@processed_refs, $evidence_item);

  }

  if (@processed_refs) {
    \@processed_refs;
  } else { return; }

}


sub seq_length {
  my $in = shift;
  my $length = length($in);
}

### Set of nested subroutines to produce to unique identifiers
# &resolver, &gene_lookup, &synbiomine_genes
# &resolver - track & serve resolved identifiers
# Calls &gene_lookup
sub resolver {
  my ($symbol, $region) = @_;
  my $gene_DBTBS = lcfirst($symbol);

  my $geneLookupRef = &gene_lookup($gene_DBTBS, $region);
  my @geneDBids = @{ $geneLookupRef } if ($geneLookupRef);

  my $geneDBidentifier;
  if ($geneLookupRef) {
    for my $identifier (@geneDBids) {
      say "Success: $gene_DBTBS resolved to $identifier" if ($debug);
      $geneDBidentifier = $identifier;
      $seen_genes{$gene_DBTBS} = $identifier unless (exists $seen_genes{$gene_DBTBS});
    }
  } else {
    warn "Fail: Nothing returned from gene lookup with: $gene_DBTBS\n" if ($debug);
    return;
  }
  
  return $geneDBidentifier;

}

# &gene_lookup - checks whether the symbol resolves to just one unique identifier
# if not, and if we have a sequence, BLAST seq, and use co-ordinates to find
 # genes using SunBioMine's web services
sub gene_lookup {

  my ($gene_DBTBS, $region) = @_;

  my ($synbioRef, @identifiers);
  if ( exists $seen_genes{$gene_DBTBS} ) {
    warn "Already seen gene: $gene_DBTBS. Reusing resolved ID...\n" if ($debug);
    push (@identifiers, $seen_genes{$gene_DBTBS});
    $synbioRef = \@identifiers;
    return $synbioRef;
  }

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

  if ( exists $id2synonym{$gene_DBTBS} ) {
    if (scalar( @{ $id2synonym{$gene_DBTBS} } > 1) ) {
      warn "$gene_DBTBS is not unique: ", join("; ", @{ $id2synonym{$gene_DBTBS} }), "\n" if ($debug);

      if ($region) {
	warn "Checking region ($extend_region) against SynBioMine...", "\n" if ($debug);

# # call a module to query synbiomine regioSearch for gene id
	my ($org_short, $geneRef) = regionSearch($extend_region);
	my @genes_synbio = @$geneRef;

	foreach my $synbio_gene (@genes_synbio) {
	  my $symbol = $synbio_gene->[0];
	  my $identifier = $synbio_gene->[1];
	  push (@identifiers, $identifier);
	  warn "Found: $gene_DBTBS matches S: $symbol\tID: $identifier\n" if ($debug);
	}

      } else {
	warn "No region - searching SynBioMine by ID...\n" if ($debug);
	my $geneRef = $id2synonym{$gene_DBTBS};
	$synbioRef = &synbiomine_genes($gene_DBTBS, $geneRef, $region);
      }

    } else {
      warn "Match: $gene_DBTBS matches: ", $id2synonym{$gene_DBTBS}->[0], "\n" if ($debug);
      my $match = $id2synonym{$gene_DBTBS}->[0];
      push (@identifiers, $match);
    }
  } else {
    warn "Can't find $gene_DBTBS in lookup. Checking SynBioMine...\n" if ($debug);
    my $geneRef = [ $gene_DBTBS ];
    $synbioRef = &synbiomine_genes($gene_DBTBS, $geneRef, $region);
  }

  $synbioRef = \@identifiers if (@identifiers);
  return $synbioRef;

}

sub synbiomine_genes {

  my ($symbol2check, $gene2check, $region) = @_;
  my $org_short = "B. subtilis subsp. subtilis str. 168";

  my @identifiers;
  foreach my $id ( @{ $gene2check} ) {

    my ($geneRef) = geneLocation($org_short, $id);
    my @gene_lookups = @$geneRef;

    if (scalar(@gene_lookups) > 1 ) {
      warn "Houston, we have an ambiguity problem: $id\n" if ($debug);
    } else {
      my $identifier = $gene_lookups[0]->[0];
      my $symbol = $gene_lookups[0]->[1];

      if ( ($symbol) && ($symbol eq $symbol2check) ) {
	warn "Symbols match: $symbol eq $symbol2check - resolving to $identifier\n" if ($debug);
	push (@identifiers, $identifier);
	return \@identifiers;
      } 
      elsif ( ($symbol) && ($symbol ne $symbol2check) ) {
	warn "Problem: Symbols don't match: $symbol eq $symbol2check - can't resolve $identifier\n" if ($debug);
#	push (@identifiers, $identifier);
      }
      else {
	warn "Ouch: $id not found in synbiomine!\n" if ($debug);
      }
    }
  }

  if (@identifiers) {
    \@identifiers;
  } else { return; }

}

######## helper subroutines:
### make gene items ###

sub gene_item {
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

sub evidence_lookup {
  
  my $evidenceRef = shift;
  my @evidence_codes = @{ $evidenceRef };

## use a heredoc to hold formatted list
# then use to poplulate a hash based on a simple RE

  my %evidence = <<END =~ /(\w+)\t(.+)/g;
AR	DNA microarray and macroarray
CH	Chromatin immunoprecipitation microarray (ChIP-on-chip)
DB	Disruption of Binding Factor gene
DP	Deletion assay
FT	Footprinting assay (DNase I, DMS, etc.)
FP	Fluorecent protein
GS	Gel retardation assay
HB	Slot blot analysis
HM	Homology search
OV	Overexpression of Binding Factor gene
PE	Primer extension analysis
RG	Reporter gene (e.g., lacZ assay)
RO	Run-off transcription assay
ROMA	Run-off transcription followed by macroarray analysis
S1	S1 mapping analysis (S1 nuclease transcript mapping)
SDM	Site-directed mutagenesis (Oligonucleotide-directed mutagenesis)
NB	Northern Blot
ND	No Data
END

  my @evidenceCode_items;
  for my $code (@evidence_codes) {
    say OUT_FILE "Code: ", $code if ($debug);
    next unless (exists $evidence{$code});

    if (exists $evidenceCode_items{$code}) {
      my $item = $evidenceCode_items{$code};
      push(@evidenceCode_items, $item);
    } 
    else {
      my $evidenceCode_item = &make_item(
	PromoterEvidenceCode => (
	  abbreviation => $code,
	  name => $evidence{$code},
	),
      );
      $evidenceCode_items{$code} = $evidenceCode_item;
      push(@evidenceCode_items, $evidenceCode_item);
    }
  }

  return \@evidenceCode_items;

}

######## helper subroutines:

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);
    if ($item->valid_field('organism')) {
        $item->set(organism => $org_item);
    }
    return $item;
}
