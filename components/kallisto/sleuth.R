if(!require("sleuth", character.only=T)) stop("Please install the sleuth package first.")
if(!require("biomaRt", character.only=T)) stop("Please install the biomaRt package first.")

args <- commandArgs(TRUE)
DESIGN_FILE <- args[1]
DATASET <- args[2]
VERSION <- args[3]
OUTPUT_FILE <- args[4]

# 3 column file-- condition, path to kallisto results, and sample ID
# The file has headers and the name of the condition column should be 'condition' for the model formula below
s2c <- read.table(DESIGN_FILE, header=T, stringsAsFactors=F)

# map the ENST IDs to common gene names 
mart=biomaRt::useMart("ENSEMBL_MART_ENSEMBL",dataset=DATASET, host=VERSION)
transcript_to_gene_map <- biomaRt::getBM(attributes = c("ensembl_transcript_id", "ensembl_gene_id",
    "external_gene_name"), mart = mart)

colnames(transcript_to_gene_map) <- c('target_id','ensemble_gene_id','gene_name')

so <- sleuth_prep(s2c, ~ condition, target_mapping = transcript_to_gene_map)
so <- sleuth_fit(so)
so <- sleuth_fit(so, ~1, 'reduced')
so <- sleuth_lrt(so, 'reduced', 'full')
results_table <-sleuth_results(so, 'reduced:full', test_type = 'lrt')

write.table(results_table, OUTPUT_FILE, sep='\t', quote=F, row.names=F)
