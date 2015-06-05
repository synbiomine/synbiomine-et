#!/usr/bin/env perl
# -*-Perl-*-

use File::Basename;
use LibSBML;
use Getopt::Std;
use strict;
use warnings;
use Data::Dumper;

use feature ':5.12';

use InterMine::Item::Document;
use InterMine::Model;

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

my $usage = "usage: @{[basename($0)]} reactions_files.sbml taxonId intermine_model_file

Script to process EBI's path2model whole genome reactions file
Writes itemsXML with reaction, pathways & gene mappings.

Note: Requires LibSBML module which isn't available from CPAN
Needs to be compiled from source with Perl bindings
See http://sbml.org/Software/libSBML

# Options
-v\tverbose output

\n";

### command line options ###
my (%opts, $verbose);

getopts('hv', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"v"} and $verbose++;

# specify and open query file (format: )
my ($reactions_file, $taxon_id, $model_file) = @ARGV;
unless ( $ARGV[2] ) { die $usage };

say "Reading \"$reactions_file\"" if ($verbose);

my $data_source_name = "Biomodels Database";
my $source_url = "http://www.ebi.ac.uk/biomodels-main";

# instantiate the model
my $im_model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(model => $im_model);

my $org_item = make_item(
    Organism => (
        taxonId => $taxon_id,
    )
);

my $data_source_item = make_item(
    DataSource => (
        name => $data_source_name,
	url => $source_url,
    ),
);

my $compound_data_set_item = make_item(
    DataSet => (
        name => "path2models compounds for taxonId $taxon_id",
	dataSource => $data_source_item,
    ),
);

my $reactions_data_set_item = make_item(
    DataSet => (
        name => "path2models reactions for taxonId $taxon_id",
	dataSource => $data_source_item,
    ),
);

my $rd = new LibSBML::SBMLReader();
my $d  = $rd->readSBML($reactions_file);

$d->printErrors();

our $model = $d->getModel();
#printAnnotation($model);

my (%species_identifiers);
my (%seen_genes, %seen_gene_items);
my (%seen_compound_items);

my $type_note = "isSetNotes";
my $type_annotation = "isSetAnnotation";

# Process all the compounds which take part in reactions
foreach my $spec ($model->getListOfSpecies()) {
  my $sboterm = $spec->getSBOTerm();
  my $species_name = $spec->getName();
  my $charge = $spec->getCharge();

# Check if the species is a modifier [Gene] ie. sboterm eq "252"
  if ( ($sboterm) && ($sboterm eq "252") ) {
    say "GeneRef: ", $spec->getId(), "  - skipping..."  if ($verbose);
    next; # if it's a gene has little info so process it as part of reaction

  } else {

  say "Processing species with Name: ", $spec->getName() if ($verbose);
    my $species_id = $spec->getId();
    $species_identifiers{$species_id}->{'sboterm'} = "0000$sboterm";
    $species_identifiers{$species_id}->{'name'} = $species_name;
    $species_identifiers{$species_id}->{'charge'} = $charge;

    my ($pid_note, $note_sb) = &process_element($type_note, $spec);
    &extract_species_IDs($pid_note, $note_sb) if ($pid_note);

    my ($pid_annot, $annot_sb) = &process_element($type_annotation, $spec);

# If no CHEBI id ... make fallback ID from supplied compound ID
    if (! $pid_annot) {

      next if ($species_id =~ /biomass_bm/);

      $species_id =~ /^(.+)_[a-z]+/;
      my $fallback_id = $1;

      $fallback_id =~ s/^bigg_/BIGG:/ if ($fallback_id =~ /^bigg_/);
      $fallback_id =~ s/^/MNXREF:/ if ($fallback_id =~ /MNX/);

      say "NO CHEBI - falling back to $fallback_id" if ($verbose);
      $species_identifiers{$species_id}->{'identifier'} = $fallback_id;

      next;
    } else {
      &extract_CHEBI($pid_annot, $annot_sb);
    }
  }
}

if ($verbose) {
  say "_**_";
  for my $key (keys %species_identifiers) {
    for my $db (keys %{ $species_identifiers{$key} } ){
      say "Key: ", $key, " Db: ", $db, " val: ", $species_identifiers{$key}->{$db};
    }
  }
  say "*__*";
}

for my $reaction ($model->getListOfReactions()) {

  say "Processing reaction with Name: ", $reaction->getName() if ($verbose);

  my $modifCheck = $reaction->getNumModifiers();
  next unless ($modifCheck);

  my $sboterm = $reaction->getSBOTerm();

# get KEGG reaction ids
  my $annot = $reaction->getAnnotationString();
  my @arr = split('\n', $annot);
  my @kegg = grep (/reaction/, @arr);
  
  # make a reaction item for each KEGG reaction
  my (@compound_ids, @reaction_compound_items, @reaction_species_items);
  for my $url (@kegg) {
    $url =~ /.+:(R.+)\".+/;
    my $kegg_reaction = $1;

    my $reaction_item = make_item(
      Reaction => (
	  identifier => $kegg_reaction,
	  type => "biochemical reaction",
	  sboterm => "0000$sboterm",
	  dataSets => [ $reactions_data_set_item ],
      ),
    );

# process Reactants and Products and push resulting compound items, ReactionSpecies items
# into arrays to plug in to the Reaction item we're making
    my ($reactantsCompoundIDref, $reactantsCompoundRef, $reactantsRefs) = &process_reaction_species("Reactants", $reaction);
    @compound_ids = @{ $reactantsCompoundIDref }; # collect reactant compound ids
    @reaction_compound_items = @{ $reactantsCompoundRef }; # collect reactant compound items
    @reaction_species_items = @{ $reactantsRefs }; # collect reactant ReactionSpecies items

    my ($productsCompoundIDref, $productsCompoundRef, $productsRefs) = &process_reaction_species("Products", $reaction);
    push( @compound_ids, @{ $productsCompoundIDref } ); # combine product and reactant compound ids
    push( @reaction_compound_items, @{ $productsCompoundRef } ); # combine product and reactant compound items
    push( @reaction_species_items, @{ $productsRefs } ); # combine product and reactant ReactionSpecies items

    $reaction_item->set( reactionSpecies => \@reaction_species_items, ); # set the ReactionSpecies collection
    $reaction_item->set( compounds => \@reaction_compound_items, ); # set the compound collection

# Now process the modifiers and add to the Reaction item 
    my $gene_items_ref = &process_modifiers($reaction); # collect modifier [gene] items
    $reaction_item->set( modifiers => $gene_items_ref, ); # set the modifier collection

# Now process kinetic parameters and add as collection to the Reaction item 
    my $paremetersRef = &process_parameters($reaction);
    $reaction_item->set( kineticParameters => $paremetersRef, ) if ($paremetersRef);

# loop over compound ids and set 'reactions' collection in compound items hash
    for my $compound_id (@compound_ids) {
      if ( exists $seen_compound_items{$compound_id} ) {
	push( @{ $seen_compound_items{$compound_id}->{'reactions'} }, $reaction_item);
      }
    }

    say "kegg: $kegg_reaction" if ($verbose);
  }

 say "*_*\n" if ($verbose);

}

$doc->close(); # writes the xml
exit(0);

### Subroutines ###
# generic routine to collect element from different twigs
sub process_element {

  my ($type, @elRef) = @_;
  my $sb = $elRef[0];
#  my $id = defined $_[1] ? $_[1] : '';

  if (not $sb->$type()) {
	return;        
  }

  my $pid = "";  
  if ($sb->isSetId()) {
      $pid = $sb->getId();
  }
  return ($pid, $sb);
}

# get identifiers from the note string
sub extract_species_IDs {
  
  my ($pid, $sb) = @_;
  unless ($sb) { 
    say "Err: No sb for $pid in note" if ($verbose);
    return };     

  my $note_string = $sb->getNotesString();
  unless ($note_string) { return };

# process note string as file handle
  open my ($note_fh), '+<', \$note_string; # process 

  while (<$note_fh>) {
    chomp;
    return if ($_ =~ m|</body>|); # get rid of the bits we don't need
    next if ($_ =~ /notes/);
    next if ($_ =~ /body/);


    $_ =~ s/^\s+//;
    $_ =~ s/<.?p>//g;

# looking for 'TEXT: value, value ...' string
    my $match = $_ =~ /(.+): (.+)/;
    next unless ($match);

    my ($database, $value_string) = ($1, $2);

# Interested in Formula and KEGG identifiers
    if ( ($database =~ /FORMULA/) and ($value_string) ) {
      
      $species_identifiers{$pid}->{'formula'} = $value_string;
    } 
    elsif ( ($database =~ /KEGG/) and ($value_string) ) {
      my @kegg_ids = split(", ", $value_string);
      my $first_kegg = $kegg_ids[0]; # first kegg is official, next ids are synonyms 
      $species_identifiers{$pid}->{'kegg'} = $first_kegg; # add it to our compound hash
    }
  }
  close ($note_fh);
}

# Need a stable ID - CHEBI seems widely used
# Bunch of CHEBI IDs in the note but definitive IDs are encoded as URLs in annotation string
# NB: not all compounds have CHBI ID - so fallback ID defined in main script: "If no CHEBI id"
sub extract_CHEBI {
  
  my ($pid, $sb) = @_;
  unless ($sb) { return };

  my $annot_string = $sb->getAnnotationString(); # process as string

  my @arr = split('\n', $annot_string);
  my @chebi_raw = grep (/CHEBI/, @arr); # grab lines with CHEBI URLs

  my $first_chebi = $chebi_raw[0]; # # first kegg is official, next ids are synonyms
  $first_chebi =~ s/^.+urn:miriam:chebi:CHEBI%3A//; # just need the ID
  $first_chebi =~ s/\".+$//;

  $species_identifiers{$pid}->{'identifier'} = "CHEBI:$first_chebi"; # set as id in compound hash

  say "CHEBI: ", $first_chebi if ($verbose);

}

# Sub for extracting and processing compounds from reactions
sub process_reaction_species {
  
  my ($type, $objects) = @_; # 'type' is either Reactants or Products

  my $role = ($type =~ /Reactants/) ? "input" : "output"; # set which side of reaction

  my $getList = "getListOf$type";

  # process reaction species
  my @species = $objects->$getList(); # list of the compounds

# define variables for holding different items [objects]
  my (@species_ids, $compound_item, @compound_items, @reaction_species_items);

# Process each compound and make a compound_item from info we stored in compound hash
  for my $element (@species) {
    my $entity = $element->getSpecies();
    my $stoichiometry = $element->getStoichiometry(); # get compound amounts

# compound info is static but need to add reaction info as new class
# 'reactionSpecies' - defines which side of equation and how much reacts
    my $reactionSpecies_item = make_item(
	ReactionSpecies => (
	    stoichiometry => $stoichiometry,
	    role => $role,
	),
    );

# lookup compound in ';make_compound_item' subroutine
# If it exists -fetch it. If not, make it - store it - fetch it
    if ( exists $species_identifiers{$entity} ) {
      say "$type: ", $entity, " Identifier:- ", $species_identifiers{$entity}->{'identifier'} if ($verbose);
      push(@species_ids, $entity);

      my $compound_item = &make_compound_item($entity);
      push(@compound_items, $compound_item); # compound item collection to add to Reaction item

      $reactionSpecies_item->set( compound => $compound_item, );
      push(@reaction_species_items, $reactionSpecies_item); # reactionSpecies item collection to add to Reaction item

    } else {
      say "Oops - can't find $type $entity in identifier look-up"; 
      next; # if we didn't find the compound - skip it
    }
  }
  # send back arrays contianing compoundIDs, items for compound and reactionSpecies
  return (\@species_ids, \@compound_items, \@reaction_species_items);
}

# Process modifiers [genes] and create Gene_item collections
sub process_modifiers {
  
  my ($objects) = shift;

  # process modifiers
  my @modifiers = $objects->getListOfModifiers();

  my @gene_items;
  for my $modifier (@modifiers) {
    my $id = $modifier->getSpecies();
    next if ($id =~ /_2_[a-z]+$/); # some IDs occur two compartments - i / e
    next if ($id =~ /MetaCyc_/); # some IDs are MetaCyc Monomers - don't need these
    $id =~ /^(.+)_.+/; # match geneID not _compartment
    my $gene = $1;

    my $gene_item;
    if (exists $seen_gene_items{$gene}) {
      say "Seen gene $gene - reusing gene item" if ($verbose);
      $gene_item = $seen_gene_items{$gene};
    } else {
      $gene_item = make_item(
	  Gene => (
	  ),
      );

# Check for E. coli MG1655 as secondary IDs used - otherwise set primary ID
      ($taxon_id ne "511145") ? $gene_item->set( primaryIdentifier => $gene, ) : $gene_item->set( secondaryIdentifier => $gene, );

      $seen_gene_items{$gene} = $gene_item;
    }
    push(@gene_items, $gene_item);
  }
  return \@gene_items;
}

# Each reaction has a set of parameters - not sure how useful they are
sub process_parameters {
  
  my $objects = shift;

  my (@parameters, %parameter_pairs);
  if ($objects->isSetKineticLaw()) {
    my $kl = $objects->getKineticLaw();
    @parameters = $kl->getListOfParameters();
  } else {
    return;
  }

# In this case, exp is 'flux balance'
  my $parameter_item = make_item(
	KineticParameters => (
	    type => "flux balance",
	),
  );

  for my $parameter (@parameters) {
    my $id = $parameter->getId();
    my $value = $parameter->getValue();

# FB has upper, lower and OC
    $parameter_pairs{'upperBound'} = $value if ($id =~ /^UPPER_BOUND/);
    $parameter_pairs{'lowerBound'} = $value if ($id =~ /^LOWER_BOUND/);
    $parameter_pairs{'fluxValue'} = $value if ($id =~ /^FLUX_VALUE/);
    $parameter_pairs{'objectiveCoefficient'} = $value if ($id =~ /^OBJECTIVE_COEFFICIENT/);

    say "Parameters: $id has value $value" if ($verbose);
  }

  for my $key (keys %parameter_pairs) {
    say "Params:  $key => $parameter_pairs{$key}" if ($verbose);
    $parameter_item->set( $key => $parameter_pairs{$key}, );
  }
  return $parameter_item;
}

######## helper subroutines:
# Replaced with process_modifiers
# # # Gene items for modifiers
# # # If we've seen it before - send it. If not, make it - store it - send it
# # sub make_gene_item {
# #   my $id = shift;
# # 
# #   my $gene_item;
# #   if (exists $seen_gene_items{$id}) {
# #     say "Seen gene $id - reusing gene item" if ($verbose);
# #     $gene_item = $seen_gene_items{$id};
# #   } else {
# #     $gene_item = make_item(
# # 	Gene => (
# # 	    primaryIdentifier => $id,
# # 	),
# #     );
# # 
# #     $seen_gene_items{$id} = $gene_item;
# #   }
# #   return $gene_item;
# # }

# Make our compound items. Again, if we've seen it before - send it. 
# If not, make it - store it - send it
sub make_compound_item {
  my $id = shift;

  my $compound_id = $species_identifiers{$id}->{'identifier'};

  my $compound_item;
  if (exists $seen_compound_items{$id}) {
    say "Seen compound $id - reusing compound item" if ($verbose);
    $compound_item = $seen_compound_items{$id};
  } else {

    my $name = $species_identifiers{$id}->{'name'}; # compound name
    my $formula = $species_identifiers{$id}->{'formula'}; # compound formula
    my $charge = $species_identifiers{$id}->{'charge'}; # compound charge
    my $sboterm = $species_identifiers{$id}->{'sboterm'}; # ontology term
    my $kegg_id = $species_identifiers{$id}->{'kegg'}; # KEGG compound ID

# Make it
    $compound_item = make_item(
	Compound => (
	    identifier => $compound_id,
	    sboterm => $sboterm,
	    dataSets => [ $compound_data_set_item ],
	),
    );

# Tests as sometimes values not set
    $compound_item->set( name => $name, ) if ($name);
    $compound_item->set( charge => $charge, ) if ($charge);
    $compound_item->set( formula => $formula, ) if ($formula);
    $compound_item->set( kegg => $kegg_id, ) if ($kegg_id);

# Store it
    $seen_compound_items{$id} = $compound_item;
  }
  return $compound_item; # Send it!
}

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);
    if ($item->valid_field('organism')) {
        $item->set(organism => $org_item);
    }
    return $item;
}

__END__
