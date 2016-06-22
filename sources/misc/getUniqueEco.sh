#!/bin/sh

# For a given set of input files, print unique ECO codes
egrep -o 'ECO:[[:digit:]]+' $* | cut -d : -f 2,3 | sort | uniq
