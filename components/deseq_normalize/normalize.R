#libraries for this script:
if(!require("DESeq", character.only=T)) stop("Please install the DESeq package first.")

# get args from the commandline:
# 1: path for a raw count matrix 
# 2: path for output normalized count matrix
# 3: a sample annotation file.  Maps the sample names to the conditions.  
#    While this file is not strictly necessary (could pass newCountDataSet a dummy vector), it's good practice
#    in case something changes. 

args<-commandArgs(TRUE)
RAW_COUNTS_FILE<-args[1]
NORMALIZED_COUNTS_FILE<-args[2]
SAMPLE_ANNOTATION_FILE<-args[3]

# read the raw count matrix:
count_data <- read.table(RAW_COUNTS_FILE, sep='\t', header = T)

#name the rows by the genes and remove that column of the dataframe
gene_names <- count_data[,1]
count_data<-count_data[-1]

# read the annotations and get the conditions in the same order as the columns of the count_data dataframe
annotations <- read.table(SAMPLE_ANNOTATION_FILE, sep='\t', header = F, row.names=1)
annotations <- annotations[colnames(count_data),]

#run the DESeq normalization:
cds=newCountDataSet(count_data, annotations)
cds=estimateSizeFactors(cds)

#write out the normalized counts:
nc<-counts( cds, normalized=TRUE )
nc<-as.data.frame(nc)
nc<-cbind(Gene=gene_names, nc)
write.table(nc, file=NORMALIZED_COUNTS_FILE, sep="\t", quote=F)
