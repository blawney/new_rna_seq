#!/bin/bash

#use bedtools:
PATH=/cccbstore-rc/projects/cccb/apps/bedtools2-2.22.1/bin/:$PATH

for BAM in $(find ../Sample_*/star_aln/ -name "*sort*.bam"); do
	BASE=$(basename $BAM ".bam")
	CVG=$BASE'.cvg'
	bedtools genomecov -ibam $BAM -bga >$CVG &
done
