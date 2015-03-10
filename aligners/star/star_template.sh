#!/bin/bash

if ! which STARstatic ; then
	echo "Could not find STAR aligner in your PATH"
	exit 1
fi

if ! which samtools ; then
	echo "Could not find samtools in your PATH"
	exit 1
fi

if ! which java ; then
	echo "Could not find Java installation in your PATH"
	exit 1
fi

#############################################################
#input variables (which will be "injected" from elsewhere)
#all paths should be absolute-- no assumptions about where
#alignments should be placed relative to the working directory

SAMPLE_DIR=%SAMPLE_DIR%
FASTQFILEA=%FASTQFILEA%
FASTQFILEB=%FASTQFILEB%
SAMPLE_NAME=%SAMPLE_NAME%
ASSEMBLY=%ASSEMBLY%
PAIRED=%PAIRED%
DEDUP=%DEDUP%
NUM0=0
NUM1=1
OUTDIR=%OUTPUTDIRECTORY%
GTF=%GTF%
GENOME_INDEX=%GENOME_INDEX% 
FINAL_BAM_FILE_SUFFIX=%BAM_FILE_SUFFIX%
PICARD_DIR=%PICARD_DIR%
FCID=%FCID%
LANE=%LANE%
INDEX=%INDEX%
#############################################################


#############################################################
#Run alignments with STAR
if [ $PAIRED -eq $NUM0 ]; then
    echo "run single-end alignment for " $SAMPLE_NAME
    STARstatic --genomeDir $GENOME_INDEX \
         --readFilesIn $FASTQFILEA \
         --runThreadN 4 \
         --readFilesCommand zcat \
         --genomeLoad NoSharedMemory \
         --sjdbGTFfile $GTF \
	 --outSAMstrandField intronMotif \
	 --outFilterIntronMotifs RemoveNoncanonical \
	 --outFilterType BySJout \
         --outFileNamePrefix $OUTDIR'/'$SAMPLE_NAME'.'
elif [ $PAIRED -eq $NUM1 ]; then
    echo "run paired alignement for " $SAMPLE_NAME
    STARstatic --genomeDir $GENOME_INDEX \
         --readFilesIn $FASTQFILEA $FASTQFILEB \
         --runThreadN 4 \
         --readFilesCommand zcat \
         --genomeLoad NoSharedMemory \
         --sjdbGTFfile $GTF \
	 --outSAMstrandField intronMotif \
	 --outFilterIntronMotifs RemoveNoncanonical \
	 --outFilterType BySJout \
         --outFileNamePrefix $OUTDIR'/'$SAMPLE_NAME'.'
else
    echo "Did not specify single- or paired-end option."
    exit 1
fi
#############################################################

#for convenience:
BASE=$OUTDIR'/'$SAMPLE_NAME
DEFAULT_SAM=$BASE'.Aligned.out.sam'  #default naming scheme by STAR
SORTED_SAM=$BASE'.sam'
UNSORTED_BAM=$BASE'.bam'
SORTED_BAM=$BASE'.sort.bam'
TMPDIR=$OUTDIR/tmp


#add read-group lines, sort, and convert to BAM:
java -Xmx8g -jar $PICARD_DIR/AddOrReplaceReadGroups.jar \
	  I=$DEFAULT_SAM \
	  o=$SORTED_BAM \
	  VALIDATION_STRINGENCY=LENIENT \
	  TMP_DIR=$TMPDIR \
	  SORT_ORDER=coordinate \
	  RGID= $FCID'.Lane'$LANE \
	  RGLB=$SAMPLE_NAME \
	  RGPL=ILLUMINA \
	  RGPU=$INDEX \
	  RGSM=$SAMPLE_NAME \
	  RGCN='CCCB'


# create index on the raw, sorted bam:
samtools index $SORTED_BAM

# make a new bam file with only primary alignments
SORTED_AND_PRIMARY_FILTERED_BAM=$BASE.sort.primary.bam
samtools view -b -F 0x0100 $SORTED_BAM > $SORTED_AND_PRIMARY_FILTERED_BAM
samtools index $SORTED_AND_PRIMARY_FILTERED_BAM

# Create a de-duped BAM file (may or may not want, but do it anyway) 	
DEDUPED_PRIMARY_SORTED_BAM=$BASE.sorted.primary.dedup.bam
	
java -Xmx8g -jar $PICARD_DIR/MarkDuplicates.jar \
	INPUT=$SORTED_AND_PRIMARY_FILTERED_BAM \
	OUTPUT=$DEDUPED_PRIMARY_SORTED_BAM \
	ASSUME_SORTED=TRUE \
	TMP_DIR=$TMPDIR \
	REMOVE_DUPLICATES=TRUE \
	METRICS_FILE=$DEDUPED_PRIMARY_SORTED_BAM.metrics.out \
	VALIDATION_STRINGENCY=LENIENT

samtools index $DEDUPED_PRIMARY_SORTED_BAM

#cleanup
rm $DEFAULT_SAM &

#remove the empty tmp directories that STAR did not cleanup
rmdir $BASE'._tmp'
rmdir $TEMPDIR

chmod 774 $OUTDIR

date

