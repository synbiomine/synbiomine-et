#!/usr/bin/env perl
use strict;
use warnings;

# we want to use say instead of print
use feature ':5.12';

# Use IM items modules
use InterMine::Item::Document;
use InterMine::Model;

my $usage = "eggNog2ItemsXML.pl <domain_set> <taxon_ID_file> <im_model_file.xml> <eggnog_data_dir> <output_items_file.xml>

Takes several files from EggNOG and produces Functional Categories,
EggNOG orthology groups and maps bacterial genes to these. Produces 
ItemsXML.

domain_set is either:
bact\tbacteria (uses bactNOG)
arch\tarchaea (uses arNOG)

Required files:
taxon_ID_file
  format: taxID1 taxID2 ... taxID
  generated: by the download scripts, fetchSynbioData.pl and fetchArchaeaData.pl
  location: data/taxons/<date_dir>/taxons_dd_mm_year.txt
im_model_file.xml
  intermine genomic model file containing the functional categories 
  model extension used in synbio-funccat (see synbio-funccat_additions)
  there is a copy in this repository (etc/funccat_model_dev.xml)
eggnog_data_dir
  path to eggnog data previously downloaded by fetchEggNogData.py
output_items_file.xml
  location to write out the generated items xml
";

my ($domain, $taxon_file, $model_file, $base_url, $items_file) = @ARGV;
unless ( $ARGV[4] ) { die $usage }

### Files to process
my $domain_set;
if ($domain eq "bact") {
  # $base_url = "/SAN_synbiomine/data/SYNBIO_data/eggnog/ParseData/";
  $domain_set = "bactNOG";
} elsif ($domain eq "arch") {
  # $base_url = "/SAN_synbiomine/data/ARCHAEA_data/eggnog/ParseData/";
  $domain_set = "arNOG";
} else {
  die "Species set should be 'bact' [bacteria] or 'arch' [archaea]\n";
}

my $id_file = $base_url . "id_conversion_taxons.txt"; ## this is a subset of id_conversion.tsv 
# that's had the relevant taxons extracted. Original file is > 3.3G!
# See the README_eggnog_files.txt for method

my $nog_members = $base_url . $domain_set . ".members.txt";
my $nog_funccat = $base_url . $domain_set . ".funccat.txt";
my $nog_description = $base_url . $domain_set . ".description.txt";
my $funccat_divisions = $base_url . "eggnogv4.funccats.txt";

my $model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(
  model => $model,
  output => $items_file
);

notify_new_activity("Adding DataSource XML");

my $data_source_item = make_item(
    DataSource => (
        name => "EggNOG: evolutionary genealogy of genes",
	url => "http://eggnog.embl.de/",
    ),
);

notify_new_activity("Adding DataSet XML");

my $ortholog_data_set_item = make_item(
    DataSet => (
        name => "EggNOG Non-supervised Orthologous Groups",
	dataSource => $data_source_item,
    ),
);

my $funccat_data_set_item = make_item(
    DataSet => (
        name => "EggNOG Functional Categories",
	dataSource => $data_source_item,
    ),
);

# set up a set of items tracking hashes
my(%seen_funccat_items, %seen_gene_items, %seen_nog_items, %seen_organism_items);

# For testing
# # my @taxon_list = qw|1392 83333 224308 1133852 691437
# #  260799 941639 1111068 592022 198094 544556 315750 272558
# #  585056 326423 685038 279010 471223 634956 585057 226900
# #  581103 649639 66692 550542 315749 398511 281309 511145
# #  420246 1367477 720555 235909 666686 315730 527000 386585 439292 585054|;

### Process Taxons file
# File format
# id1 id2 id3 ... id(n)

notify_new_activity("Loading taxon mappings");

say "Processing file $taxon_file";

open my $taxons_fh, "$taxon_file" or die "can't open file: $taxon_file $!\n";
my @taxon_list = split(" ", <$taxons_fh>);
close ($taxons_fh);

### Process functional categories file
# eggnogv4.funccats.txt File format
# INFORMATION STORAGE AND PROCESSING
#  [J] Translation, ribosomal structure and biogenesis 
#  [A] RNA processing and modification 
#  [K] Transcription 
#  [L] Replication, recombination and repair 
#  [B] Chromatin structure and dynamics 
# 
# split on empty line

notify_new_activity("Adding FunctionalCategory XML");

open my $funccat_fh, "$funccat_divisions" or die "can't open file: $funccat_divisions $!\n";

say "Processing file $funccat_divisions";

my @cats = do { local $/ = ''; <$funccat_fh> }; # split filehandle on empty line into array

my %major_funccat;
for my $cat (@cats) {
  my @cat_divisions = split("\n", $cat);

  my $division = shift(@cat_divisions);

  for my $category (@cat_divisions) {
    my ($letter, $description) = split('] ', $category);
    $letter =~ s/ \[//;
    $description =~ s/ $//;
    $major_funccat{$letter} = [ lc($description), lc($division) ];
    
    make_funccat_items($letter, lc($description), lc($division), $funccat_data_set_item);
  }
}
close ($funccat_fh);


### Process EggNOG descriptions file
# File format
# EggNogID \t category description

notify_new_activity("Adding EggNogCategory XML");

my %nog_descriptions;
open my $nogdesc_fh, "$nog_description" or die "can't open file: $nog_description $!\n";

say "Processing file $nog_description";

while (<$nogdesc_fh>) {
  chomp;
  my ($nogID, $description) = split("\t", $_);
  $description = ($description) ? $description : "No description";
  $nog_descriptions{$nogID} = $description;

  make_nogDesc_item($nogID, $description, $ortholog_data_set_item);
}

close ($nogdesc_fh);

### Process file which maps EggNogIDs to functional categories
# File format
# EggNogID \t AB    [joined_classifiers - belongs to categories A & B ]

notify_new_activity("Loading EggNogID -> Functional Category mappings");

my (%funccats);
open my $nogCat_fh, "$nog_funccat" or die "can't open file: $nog_funccat $!\n";

say "Processing file $nog_funccat";

while (<$nogCat_fh>) {
  chomp;
  my ($nog_cat, $funccats) = split("\t");

  my @cats;
  if ( length($funccats) > 1 ) {
    @cats = split('', $funccats);
  } else {
    push(@cats, $funccats);
  }
  $funccats{$nog_cat} = \@cats;
}

close ($nogCat_fh);

for my $key (keys %funccats) {
  for my $category ( @{ $funccats{$key} } ) {
    my $category_item = $seen_funccat_items{$category} if ( exists $seen_funccat_items{$category} );

    if ( exists $seen_nog_items{$key} ) {
      push( @{ $seen_nog_items{$key}->{'functionalCategories'} }, $category_item );

      my $nog_item = $seen_nog_items{$key};
      push( @{ $seen_funccat_items{$category}->{'eggNogCategories'} }, $nog_item );
    }
  }
}

### Process ID conversion file 
# This contains mappings of eggNog organism identifiers to stable organism ID
# File format:
# taxID \t eggNogOrgID \t stableID \t source
# 224308  Bsubs1_010100000080     bsu:BSU00160    BLAST_KEGG_ID
# I've chosen BLAST_KEGG_ID as these correspond to genbank unique locus_tag identifiers

notify_new_activity("Loading organism ID mappings");

my (%id_lookup);
open my $id_fh, "$id_file" or die "can't open file: $id_file $!\n";

say "Processing file $id_file";

while (<$id_fh>) {
  chomp $_;

  my ($taxon_id, $nog_id, $kegg_id, undef) = split("\t", $_);
  my ($kegg_org, $org_id) = split(":", $kegg_id);
  my $taxon_nogID = $taxon_id . "\." . $nog_id;

  # say "Adding id mapping $taxon_nogID => $org_id";
  $id_lookup{$taxon_nogID} = $org_id;
}

say "Added " . scalar(keys(%id_lookup)) . " mappings";

close ($id_fh);

### Process file of NOG nog_members
# File format:
# EggNogID \t taxon.eggNogOrgID \t prot_start \t prot_end
# We use this with the ID conversion file above to resolve
# orthologue group members to their stable gene IDs

notify_new_activity("Adding Gene XML");

open my $nog_fh, "$nog_members" or die "can't open file: $nog_members $!\n";

say "Processing file $nog_members";

while (<$nog_fh>) {
  chomp $_;
  
  my ($nog_cat, $member_nog_id, $start, $end) = split("\t", $_);
  my ($taxon, $nog_id) = split('\.', $member_nog_id);

#  say "Looking for id $member_nog_id";

  if ( exists $id_lookup{$member_nog_id} ) {
    my $gene_id = $id_lookup{$member_nog_id};

    my $gene_item = make_gene_item($gene_id, $taxon);

    if ( exists $seen_nog_items{$nog_cat} ) {
      push( @{ $seen_nog_items{$nog_cat}->{'genes'} }, $gene_item );

      my $nog_item = $seen_nog_items{$nog_cat};
      push( @{ $seen_gene_items{$gene_id}->{'eggNogCategories'} }, $nog_item );
    }

#    say $nog_cat, " ", $taxon, " ", $id_lookup{$member_nog_id};
  }
}


close ($nog_fh);


$doc->close(); # writes the xml
exit(0);

######### helper subroutines:

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);
#     if ($item->valid_field('organism')) {
#         $item->set(organism => $org_item);
#     }
    return $item;
}

sub make_funccat_items {
  my($letter, $description, $division, $funccat_data_set_item) = @_;
  my $funccat_item = make_item(
    FunctionalCategory => (
      classifier => $letter,
      name => $description,
      category => $division,
      dataSets => [$funccat_data_set_item], 
    ),
  );

  $seen_funccat_items{$letter} = $funccat_item;

}

sub make_nogDesc_item {

  my ($nogID, $description, $ortholog_data_set_item) = @_;
  my $nogDesc_item = make_item(
    EggNogCategory => (
      primaryIdentifier => $nogID,
      description => $description,
      dataSets => [$ortholog_data_set_item], 
    ),
  );

  $seen_nog_items{$nogID} = $nogDesc_item;

}

sub make_organism_item {
  my $org_item;
  my $taxon = shift;
  
  if ( exists $seen_organism_items{$taxon} ) {
    $org_item = $seen_organism_items{$taxon};
  } else {
    $org_item = make_item(
      Organism => (
        taxonId => $taxon,
      ),
    );
    $seen_organism_items{$taxon} = $org_item;
  }

  return $org_item;
}

sub make_gene_item {
  my $gene_item;
  my ($gene_id, $taxon) = @_;

  my $org_item = make_organism_item($taxon);
    
  if ( exists $seen_gene_items{$gene_id} ) {
       $gene_item = $seen_gene_items{$gene_id};
  } else {
    $gene_item = make_item(
      Gene => (
        primaryIdentifier => $gene_id,
        organism => $org_item,
      ),
    );
    $seen_gene_items{$gene_id} = $gene_item;
  }

  return $gene_item;
}

=pod
Provide an eye-catching way of showing when we engage in different activities in this script
=cut
sub notify_new_activity {
  my ($activity) = @_; 

  say "~~~ $activity ~~~";
}
