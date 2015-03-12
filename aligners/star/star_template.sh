#!/bin/bash

if ! which java ; then
	echo "Could not find Java installation in your PATH"
	exit 1
fi

#############################################################
#input variables (which will be "injected" from elsewhere)
#all paths should be absolute-- no assumptions about where
#alignments should be placed relative to the working directory

STAR=%STAR%
SAMTOOLS=%SAMTOOLS%
PICARD_DIR=%PICARD_DIR%

FASTQFILEA=%FASTQFILEA%
FASTQFILEB=%FASTQFILEB%
SAMPLE_NAME=%SAMPLE_NAME%
PAIRED=%PAIRED%
OUTDIR=%OUTDIR%
GTF=%GTF%
GENOME_INDEX=%GENOME_INDEX% 
FCID=%FCID%
LANE=%LANE%
INDEX=%INDEX%
#############################################################

# for convenience
NUM0=0
NUM1=1

#############################################################
#Run alignments with STAR
if [ $PAIRED -eq $NUM0 ]; then
    echo "run single-end alignment for " $SAMPLE_NAME
    $STAR --genomeDir $GENOME_INDEX \
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
    $STAR --genomeDir $GENOME_INDEX \
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
$SAMTOOLS index $SORTED_BAM

# make a new bam file with only primary alignments
SORTED_AND_PRIMARY_FILTERED_BAM=$BASE.sort.primary.bam
$SAMTOOLS view -b -F 0x0100 $SORTED_BAM > $SORTED_AND_PRIMARY_FILTERED_BAM
$SAMTOOLS index $SORTED_AND_PRIMARY_FILTERED_BAM

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

$SAMTOOLS index $DEDUPED_PRIMARY_SORTED_BAM

#cleanup
rm $DEFAULT_SAM &

#remove the empty tmp directories that STAR did not cleanup
rmdir $BASE'._tmp'
rmdir $TEMPDIR

chmod 774 $OUTDIR

date

