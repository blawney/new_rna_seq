import matplotlib.pyplot as plt
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


#TODO: write this method!
def plot_coverage():
	pass
