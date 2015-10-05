import logging
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
import numpy as np
import matplotlib.patches as mpatches
import glob
import os

class CoverageFileNotFoundException(Exception):
	pass

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
	N = len(plot_data[plot_data.keys()[0]].keys())
	width = 10.0
	height = 0.8 * N
	fig = plt.figure(figsize=(width, height))
	ax = fig.add_subplot(111)
	y_pos = np.arange(N)

	legend_handles = []
	bam_types = sorted(plot_data.keys(), comparer)
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

	all_regions = project.parameters.get('chromosomes')

	# define the number of rows/cols for the 'grid' of coverage figures
	n=len(all_regions)
	num_cols = 3
	num_rows = n/num_cols+1

	for sample in project.samples:
		logging.info('globbing path: %s' % os.path.join( component_params.get('report_output_dir'), sample.sample_name + '.' + component_params.get('bam_filter_level') + '.'  + component_params.get('coverage_file_suffix')))
		cvg_glob = glob.glob(os.path.join( component_params.get('report_output_dir'), sample.sample_name + '.' + component_params.get('bam_filter_level') + '.' + component_params.get('coverage_file_suffix')))
		if len(cvg_glob) == 1:
			cvg_filepath = cvg_glob[0]
			logging.info('For sample %s, found cvg file: %s' % (sample.sample_name, cvg_filepath))
			data = pd.read_table(cvg_filepath, names=['chrom', 'start', 'end', 'counts'], dtype={'chrom':str, 'start':np.int32, 'end':np.int32, 'counts':np.int32}, low_memory=False)

			fig = plt.figure(figsize=(22,22))

			for i,c in enumerate(all_regions):
				chr_data = data[data.chrom == c]
				L = chr_data.shape[0]
				
				ax = fig.add_subplot(num_rows, num_cols, i+1)
				xvals = np.zeros(2*L)
				xvals[0] = chr_data.start.iloc[0]
				xvals[-1] = chr_data.end.iloc[-1]
				xvals[1:-1] = np.repeat(chr_data.end.iloc[:-1].values,2)

				yvals = np.repeat(chr_data.counts.values,2)
				ax.plot(xvals,yvals)
				ax.set_ylim((0, 1.05 * np.max(yvals)))
				if i==0:
					ax.set_ylabel('Depth')
				ax.set_title(c)
				ax.set_xticks([])
			plt.tight_layout()
			output_plot = cvg_filepath[:-len(component_params.get('coverage_file_suffix'))] + component_params.get('coverage_plot_suffix')
			logging.info('Write coverage pdf to %s' % output_plot)
			plt.savefig(output_plot)
		else:
			raise CoverageFileNotFoundException('Coverage file could not be found for sample %s' % sample.sample_name)




