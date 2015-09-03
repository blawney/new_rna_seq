import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
import numpy as np
import matplotlib.patches as mpatches

# some reasonable colors for this plot
colors = ["#24476B", "#90BA6E", "#9F5845"]
rcParams['font.size'] = 12.0

# a method for sorting strings based on length
comparer = lambda x,y: -1 if len(x) < len(y) else 1

def plot_bam_counts(plot_data, filename):
	"""
	plot_data is a dictionary of nested dictionaries.  The first level of the mapping has the BAM 'level' (e.g. sorted, deduped, etc)
	mapping to a dictionary of sample-to-integer key-value pairs.  filename is just the full path to the output figure
	"""

	N = len(samples)
	width = 10.0
	height = 0.8 * N
	fig = plt.figure(figsize=(width, height))
	ax = fig.add_subplot(111)
	y_pos = np.arange(N)

	legend_handles = []
	bam_types = plot_data.keys().sort(comparer)
	for i,bam_level in enumerate(bam_types):
		counts_dict = plot_data[bam_level]
		samples = sorted(counts_dict.keys())
		points = [ counts_dict[s] for s in samples ]
		legend_handles.append(mpatches.Patch(color=colors[i], alpha=(0.4+0.3*i),label=bam_level))
		ax.fill_betweenx(y_pos, points, color = colors[i], alpha=(0.4+0.3*i))

	ax.yaxis.set_ticks(y_pos)
	ax.yaxis.set_ticklabels(samples)
	ax.yaxis.set_tick_params(pad=10)
	ax.set_ylim([-0.75, N-0.25])
	ax.xaxis.grid(True)
	ax.yaxis.grid(True)


	font={'family': 'serif', 'size':16}
	plt.rc("font", **font)
	ax.set_title('BAM File Read Counts')
	ax.legend(handles=legend_handles, loc=9,  bbox_to_anchor=(0.5, -0.05))

	fig.savefig( filename, bbox_inches='tight')


def plot_coverage(project, component_params):

	#TODO: change this to accomodate different genomes! (do they have chr prefix?  mouse and human with different number of chr)

	# define the 'usual' chromosomes to plot (skip unplaced contigs, etc)
	chromosomes = range(1,20)
	chromosomes = ['chr'+str(s) for s in chromosomes]
	chromosomes.append('chrX')
	chromosomes.append('chrY')

	all_regions = [s for s in chromosomes]
	all_regions.append('chrM')

	# define the number of rows/cols for the 'grid' of coverage figures
	n=len(all_regions)
	num_cols = 3
	num_rows = n/num_cols+1

	for sample in project.samples:
		cvg_glob = glob.glob(os.path.join( component_params.get('report_output_dir'), sample.sample_name + '*' + component_params.get('coverage_file_suffix'))
		if len(cvg_glob) == 1:
			cvg_filepath = cvg_glob[0]
			data = pd.read_table(cvg_filepath, names=['chrom', 'start', 'end', 'counts'])
			max_cvg = np.max(data[data['chrom'].isin(chromosomes)].counts)

			fig = plt.figure(figsize=(22,22))

			for i,c in enumerate(all_regions):
				chr_data = data[data.chrom == c]
				ax = fig.add_subplot(num_rows, num_cols, i+1)
				x=chr_data.start
				y=chr_data.counts
				ax.plot(x,y)
				if c in chromosomes:
				    ax.set_ylim((0,max_cvg))
				else:
				    ax.set_ylim((0,np.max(y)))
				ax.set_title(c)
				ax.set_xticks([])

			plt.tight_layout() 
			plt.savefig(str(g)+".pdf", format="pdf")





