#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Std;
require LWP::UserAgent;

use feature ':5.12';

use InterMine::Item::Document;
use InterMine::Model;

# Print unicode to standard out
binmode(STDOUT, 'utf8');
# Silence warnings when printing null fields
no warnings ('uninitialized');

my $usage = "usage: $0 intermine_model_file output_directory_path

Script to retrieve KEGG reactions and associated pathways
Writes an items XML with reaction/ pathway mappings

# Options
-v\tverbose output

\n";

### command line options ###
my (%opts, $verbose);

getopts('hv', \%opts);
defined $opts{"h"} and die $usage;
defined $opts{"v"} and $verbose++;

unless ( $ARGV[0] ) { die $usage };

my ($model_file, $out_dir) = @ARGV;
$out_dir = ($out_dir) ? $out_dir : "\.";

my $data_source_name = "GenomeNet";
my $kegg_url = "http://www.kegg.jp/";

# instantiate the model
my $model = new InterMine::Model(file => $model_file);
my $doc = new InterMine::Item::Document(model => $model);


my $data_source_item = make_item(
    DataSource => (
        name => $data_source_name,
	url => $kegg_url,
    ),
);

my $reactions_data_set_item = make_item(
    DataSet => (
        name => "KEGG reactions data set",
	dataSource => $data_source_item,
    ),
);

say "Executing KEGG pathways script" if ($verbose);

# Process reactions
my (%seen_reaction_items);
my $react_url = "http://rest.kegg.jp/list/reaction";
my $reactions = &kegg_ws($react_url);
&process_reactions($reactions);

# Process Reaction to Pathways mappings
my (%seen_pathway_items);
my $react2path_url = "http://rest.kegg.jp/link/pathway/reaction";
my $mappings = &kegg_ws($react2path_url);
&process_mappings($mappings);

$doc->close(); # writes the xml
exit(0);

say "All done - enjoy your results" if ($verbose);
exit(0);

## sub routines ##
# set up the user agent and request - return the content
sub kegg_ws {

  my $url = shift;

  my $agent = LWP::UserAgent->new;

  my $request  = HTTP::Request->new(GET => $url);
  my $response = $agent->request($request);

  $response->is_success or say "Error: " . 
  $response->code . " " . $response->message;

  return $response->content;

}

# process the reaction content as a file handle
sub process_reactions {

  my ($content) = shift;

  open my ($str_fh), '+<', \$content; # process 

  while (<$str_fh>) {
    chomp;
    $_ =~ s/^rn://; # remove reaction prefix
    my ($reaction, $nameString) = split("\t", $_); # separate reaction id and name part
    say "line $reaction $nameString" if ($verbose);

# test to see if we have a two-part description [ name; equation ]
# if two-part, set name and equation - else we'll just use nameString for both
    my ($name, $equation) = ($1, $2) if ($nameString =~ /(.+); (.+)/);

# make the reaction items
    my $reaction_item = make_item(
      Reaction => (
	identifier => $reaction,
	dataSets => [ $reactions_data_set_item ],
      ),
    );

    if ($equation) {
      	$reaction_item->set( name => $name, );
	$reaction_item->set( equation => $equation, );
    } else {
      $reaction_item->set( name => $nameString, );
      $reaction_item->set( equation => $nameString, );
    }
    $seen_reaction_items{$reaction} = $reaction_item; # add to hash for re-use
  }

  close ($str_fh); # close the reactions file handle
}

# process the reaction/ pathway mapping content as a file handle
sub process_mappings {

  my ($content) = shift;

  open my ($str_fh), '+<', \$content; # assign content to file handle 

# loop over content
  while (<$str_fh>) {
    chomp;
    next if ($_ =~ /map/);
    $_ =~ s/path://; # strip prefixes
    $_ =~ s/rn:?//g;

    my ($reaction, $pathway) = split("\t", $_); # split
    say "line $reaction - $pathway" if ($verbose);

    my $reaction_item = &fetch_reaction_item($reaction); # fetch the reaction item
    next unless $reaction_item; # skip if the reaction item doesn't exist

    my $pathway_item = &make_pathway_item($pathway, $reaction_item); # make our pathway item
    if ($pathway_item) {
    push( @{ $reaction_item->{'pathways'} }, $pathway_item); # append pathway item to pathways collection
    } else {
      warn "Ooops! didn't find a pathway item for $pathway\n";
    }
  }

  close ($str_fh); # close the pathway/reactions file handle
}

######## helper subroutines:

sub make_item {
    my @args = @_;
    my $item = $doc->add_item(@args);

# we're organism agnostic
#    if ($item->valid_field('organism')) {  
#        $item->set(organism => $org_item);
#    }
    return $item;
}

# check to see whether we've made a reaction items for that ID
sub fetch_reaction_item {
  my $id = shift;

  my $reaction_item;
  if (exists $seen_reaction_items{$id}) {
    $reaction_item = $seen_reaction_items{$id}; # if we have, assign it
  } else {
    warn "Error: no reaction found for $id\n"; # if not, report the error
    return;
  }
  return $reaction_item; # return the reaction item
}


sub make_pathway_item {
  my ($id, $reaction_item) = @_;

  my $pathway_item;

# check to see whether we've made a pathway item for that ID
  if (exists $seen_pathway_items{$id}) {
    say "Processing pathway $id" if ($verbose);

# pathway items have a collection of reactions
    push( @{ $seen_pathway_items{$id} ->{'reactions'} }, $reaction_item);
    $pathway_item = $seen_pathway_items{$id}; # if we have, assign it
  } else {
# if not, report the error and make a new one
    say "Haven't seen pathway $id - making one" if ($verbose);
    $pathway_item = make_item(
      Pathway => (
	identifier => $id,
	reactions => [ $reaction_item ],
      ),
    );
    $seen_pathway_items{$id} = $pathway_item;  #assign the new one
  }
  return $pathway_item; # return the pathway item
}