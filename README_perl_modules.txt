ML’s SynBioMine WS modules:

BlastSynbio.pm
syntax: use BlastSynbio qw/run_BLAST/      [BLASTN against genome and return coordinates]
Requires: path_to_blast_query_file, seq_length, path_to_blastdb_dir, debug_value
path_to_blast_query_file = 
path_to_blast_dir = /SAN_synbiomine/data/SYNBIO_data/BLAST
debug_value = 1 (setting $debug to 1 gives verbose output)

SynbioGene2Location.pm
syntax: use SynbioGene2Location qw/geneLocation/  [For a given gene, returns the chrm location]
Requires: org_short_name, gene_id
Returns: a reference to an array of [gene_ids, symbol, location, org short name] (may be empty if no gene found)

SynbioRegionSearch.pm
syntax: SynbioRegionSearch qw/regionSearch/  [For a given set of coordinates - returns the nearest gene]
Requires: chrm_region in format: chrm:start..end
Returns: organsim short name and a reference to an array of gene_ids [symbol, identifier] (may be empty if no gene found)
