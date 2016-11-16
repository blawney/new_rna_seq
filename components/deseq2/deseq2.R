if(!require("DESeq2", character.only=T)) stop("Please install the DESeq2 package first.")
if(!require("RColorBrewer", character.only=T)) stop("Please install the RColorBrewer package first.")
if(!require("gplots", character.only=T)) stop("Please install the gplots package first.")

# args from command line:
args<-commandArgs(TRUE)
RAW_COUNT_MATRIX<-args[1]
SAMPLE_ANNOTATION_FILE<-args[2]
CONDITION_A<-args[3]
CONDITION_B<-args[4]
OUTPUT_DESEQ_FILE <- args[5] #full path
OUTPUT_HEATMAP_FILE <- args[6] #full path
NUM_GENES<-as.integer(args[7])


# read the raw count matrix, genes as row names:
count_data <- read.table(RAW_COUNT_MATRIX, sep='\t', header = T, row.names = 1, stringsAsFactors = F)

# read the annotations
annotations <- read.table(SAMPLE_ANNOTATION_FILE, sep='\t', header = F, col.names = c('sample','condition'), stringsAsFactors = F)

# Keep only the rows that concern our contrast of interest
# Could keep it all together, but this is more explicit
selected_groups<-c(CONDITION_A, CONDITION_B)
annotations<-annotations[annotations$condition %in% selected_groups,]

# subset to only keep samples corresponding to the current groups in the count_data dataframe
count_data <- count_data[,annotations$sample]

# DESeq2 expects that the rownames of the annotation data frame are the sample names.  Set the rownames and drop that col
rownames(annotations) <- annotations$sample
annotations <- annotations[-1]

# Need to set the condition as a factor since it's going to be used as a design matrix
annotations$condition <- as.factor(annotations$condition)


dds <- DESeqDataSetFromMatrix(countData = count_data,
							  colData = annotations,
							  design = ~condition)

dds <- DESeq(dds)
res <- results(dds)
resOrdered <- res[order(res$padj),]
write.table(resOrdered, OUTPUT_DESEQ_FILE, sep=',', quote=F)

######### For creating contrast-level heatmap ######################

#produce a heatmap of the normalized counts, using the variance-stabilizing transformation:
vsd <- varianceStabilizingTransformation(dds, blind=FALSE)
nc<-assay(vsd)
select<-order(res$padj)[1:NUM_GENES]
heatmapcols<-colorRampPalette(brewer.pal(9, "GnBu"))(100)

#set the longest dimension of the image:
shortest_dimension<-1200 #pixels
sample_count<-ncol(vsd)
ratio<-0.25*NUM_GENES/sample_count

#most of the time there will be more genes than samples
#set the aspect ratio of the heatmap accordingly
h<-shortest_dimension*ratio
w<-shortest_dimension

#however, if more samples than genes, switch the dimensions so it looks reasonable:
if (ratio < 1)
{
	temp<-w
	w<-h
	h<-temp
}

# adjust the text size to be reasonable with the size of the heatmap
text_size = 1.5+1/log10(NUM_GENES)

#write the heatmap as a png:
png(filename=OUTPUT_HEATMAP_FILE, width=w, height=h, units="px")
heatmap.2(nc[select,], col=heatmapcols, trace="none", margin=c(25,12), cexRow=text_size, cexCol=text_size)
dev.off()
