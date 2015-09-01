import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
import matplotlib.patches as mpatches

colors = ["#24476B", "#90BA6E", "#9F5845"]
rcParams['font.size'] = 12.0

def plot_bam_counts():
	#TODO: determine args to this method.  Complete it.
	N = len(samples)
	width = 10.0
	height = 0.8* N
	fig = plt.figure(figsize=(width, height))
	ax = fig.add_subplot(111)
	y_pos = np.arange(N)

	legend_handles = []
	for i,t in enumerate(types):
		counts = count_dict[t]
		points = [ counts[d] for d in samples ]
		legend_handles.append(mpatches.Patch(color=colors[i], alpha=(0.4+0.3*i),label=t))
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

	fig.savefig('bam_counts.pdf', bbox_inches='tight')

