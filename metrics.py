import numpy as np
import networkx as nx
from collections import defaultdict

def pageRank(G, harm, alpha=0.85):
	return nx.pagerank(G, alpha=alpha, personalization=harm)

def alphaCentrality(G, harm, alpha=0.1):
	return nx.katz_centrality(G, alpha=alpha, beta=harm)

allpaths = [ -1, '', None, defaultdict(list) ] #<-- format is  { length1:[origin1, origin2, ...], length2:[origin1, ...], ...}

def resetPaths(): 
	allpaths[0] = -1
	allpaths[1] = ''
	allpaths[2] = None
	allpaths[3] = defaultdict(list)
		
def pathCount(G, target, direction='in', pathfunc=nx.all_simple_paths, recompute=False):


	if allpaths[0] != target or allpaths[1] != direction or allpaths[2] != pathfunc or recompute:
		allpaths[0] = target
		allpaths[1] = direction
		allpaths[2] = pathfunc
		allpaths[3] = defaultdict(list)
		for n in G.nodes():
			if n == target: continue
			if direction == 'in':
				if not nx.has_path(G, n, target): continue
				for p in pathfunc(G, n, target):
					allpaths[3][ len(p)-1 ].append( n )
			elif direction == 'out':
				if not nx.has_path(G, target, n): continue
				for p in pathfunc(G, target, n):
					allpaths[3][ len(p)-1 ].append( n )

def alphaMax(x, alpha):
	return np.max( [ ( alpha**i )*x[i] for i in range(len(x)) ] )
			
def alphaMean(x, alpha):
	return np.average(x, weights=[ alpha**i for i in range(len(x)) ])
	
def topCountMean(x, k):
	if len(x) < k: return np.mean(x)
	return np.mean( sorted(x, reverse=True)[:k] )
		
def topkMean(x, k):
	x = np.asarray(x)	
	cutoff = np.percentile(x, k, method='linear')
	return x[ x >= cutoff ].mean()

def topkAlphaMean(x, k, alpha):
	x = np.asarray(x)	
	cutoff = np.percentile(x, k, method='linear')
	return alphaMean( x[ x >= cutoff ], alpha )
	
	
def upstreamHarm(G, target, harm, m, agg=np.max, path_counting="all", direction='in'):

	if m == 0:
		return 0
	if path_counting == 'all':
		pathCount(G, target, direction=direction, pathfunc=nx.all_simple_paths)
	elif path_counting == 'allshortest':
		pathCount(G, target, direction=direction, pathfunc=nx.all_shortest_paths)
	elif path_counting == 'shortest':
		pathCount(G, target, direction=direction, pathfunc=nx.all_shortest_paths)
		for i in allpaths[3].keys(): allpaths[3][i] = list( set(allpaths[3][i]) )
			
	harms_at_level = [ harm[i] for i in allpaths[3][m] ] 
	if harms_at_level:
		return agg( harms_at_level )
	return 0

def truncate_at_last_nonzero(x):
    nz = np.nonzero(x)[0]
    return x[:nz[-1] + 1] if len(nz) else x[:0]
    
def networkHarm(G, target, harm, m_max=None, outer_agg=np.max, inner_agg=np.max, path_counting="all", direction='in' ):
	
	if path_counting == 'all':
		pathCount(G, target, direction=direction, pathfunc=nx.all_simple_paths)
	elif path_counting == 'allshortest':
		pathCount(G, target, direction=direction, pathfunc=nx.all_shortest_paths)
	elif path_counting == 'shortest':
		pathCount(G, target, direction=direction, pathfunc=nx.all_shortest_paths)
		for i in allpaths[3].keys(): allpaths[3][i] = list( set(allpaths[3][i]) )
	else:
		print("Path counting type:", path_counting, "not implemented")
		exit(1)
	
	if len(allpaths[3]) == 0: return 0
	
	if not m_max: m_max = max(allpaths[3].keys())+1
	uharms = truncate_at_last_nonzero( [  upstreamHarm(G, target, harm, m, agg=inner_agg, path_counting=path_counting, direction=direction) for m in range(1, m_max ) ] )
	if uharms:
		return outer_agg( uharms )
	return 0
	
def vulnerability(G, target, alter, harm, H0=None, m_max=5, outer_agg=np.max, inner_agg=np.max, path_counting="all", direction='in' ):
	
	
	if target == alter: return 0
	orig = harm[alter]

	if not H0:
		resetPaths()			
		H0 = networkHarm(G, target, harm, outer_agg=outer_agg, inner_agg=inner_agg, path_counting=path_counting, direction=direction)

	harm[alter] = 100
	H1 = networkHarm(G, target, harm, outer_agg=outer_agg, inner_agg=inner_agg, path_counting=path_counting, direction=direction)
	harm[alter] = orig

	return H1-H0
	
def influence(G, target, alter, harm, H0=None, m_max=5, outer_agg=np.max, inner_agg=np.max, path_counting="all", direction='in' ):
	
	if target == alter: return 0
	
	if not H0:
		resetPaths()	
		H0 = networkHarm(G, target, harm, outer_agg=outer_agg, inner_agg=inner_agg, path_counting=path_counting, direction=direction)

	G2 = G.copy()
	G2.remove_node(alter)
	resetPaths()	
	H1 = networkHarm(G2, target, harm, outer_agg=outer_agg, inner_agg=inner_agg, path_counting=path_counting, direction=direction)

	return H1-H0
					
			


if __name__ == "__main__":
	import matplotlib.pyplot as plt
	from matplotlib import colors
	from matplotlib.gridspec import GridSpec
	import matplotlib as mpl

	G = nx.DiGraph()

	G.add_edge(1,0)
	G.add_edge(2,0)
	G.add_edge(3,0)
	G.add_edge(0,3)
	G.add_edge(4,0)
	G.add_edge(5,0)
	G.add_edge(0,5)
	G.add_edge(1,2)
	G.add_edge(2,1)


	G.add_edge(6,3)
	G.add_edge(3,6)
	G.add_edge(7,3)
	G.add_edge(8,4)
	G.add_edge(4,8)
	G.add_edge(9,3)
	G.add_edge(3,9)
	G.add_edge(9,4)
	G.add_edge(9,8)


	G.add_edge(10,6)
	G.add_edge(10,7)
	G.add_edge(10,3)
	G.add_edge(8,10)
	G.add_edge(3,8)
	G.add_edge(11,9)
	G.add_edge(12,9)
													

	harm = { 0 : 0,
	1 : 10,
	2 : 55,
	3 : 50, 
	4 : 50,
	5 : 50,
	6 : 50,
	7 : 90,
	8 : 50,
	9 : 50,
	10 : 75,
	11 : 50,
	12 : 100,
	}

	alphaMean85 = lambda x : alphaMean(x, 0.85)
	alphaMax85 = lambda x : alphaMax(x, 0.85)

	
	print( "pageRank", pageRank(G, harm) )
	print( "alphaCentrality", alphaCentrality(G, harm) )

	target = 0;
	for pathtype in ["all", "allshortest", "shortest"]:
		resetPaths()
		for name,fn in {"MAX":np.max, "AVG":np.mean}.items():
			for m in range(1,4):
				print( "upstreamHarm_{}_{}^{}".format(pathtype, name, m), round(upstreamHarm(G, target, harm, m, agg=fn, path_counting=pathtype, direction="in")) )
	
	resetPaths()
	for outer_name,outer_fn in {"MAX":alphaMax85, "AVG":alphaMean85}.items():
		for inner_name,inner_fn in {"MAX":np.max, "AVG":np.mean}.items():
			print( 'networkHarm_all_{}_{}'.format(outer_name, inner_name), round(networkHarm(G, target, harm, outer_agg=outer_fn, inner_agg=inner_fn)) )
	
			
	##Make some nice plots
	N1 = 5
	N2 = 4
	N3 = 3
	pos = { 0 : np.array([0,0]) }

	for i in range(N1): pos[1+i] = np.array([i-(N1//2),1])
	for i in range(N2): pos[1+N1+i] = np.array([i-(N2//2),2])
	for i in range(N3): pos[1+N1+N2+i] = np.array([i-(N3//2),3])

	fig = plt.figure(figsize=(16, 8) , layout="constrained")
	gs = GridSpec(5,4,fig, height_ratios=[1, 1, 1, 1, 0.15])

	ax1 = fig.add_subplot(gs[:4, :2])
	nx.draw_networkx_nodes(G, pos, ax=ax1, edgecolors='k', linewidths=3, node_size=1500, cmap='Reds', vmin=0, vmax=100, nodelist=range(len(G.nodes)), node_color=[harm[i] for i in range(len(G.nodes))])
	nx.draw_networkx_edges(G, pos, ax=ax1, width=3, node_size=1500, arrowsize=30)
	nx.draw_networkx_labels(G, pos, ax=ax1, font_size=20, font_weight='bold', labels={ i:'{}'.format(h) for i,h in harm.items()} )

	norm = mpl.colors.Normalize(vmin=0, vmax=100)
	sm = mpl.cm.ScalarMappable(cmap="Reds", norm=norm)
	sm.set_array([]) 
	cax = fig.add_subplot(gs[4, :2])
	fig.colorbar(sm, cax=cax, orientation="horizontal")



	ax = [
	[fig.add_subplot(gs[0:2,2]), fig.add_subplot(gs[0:2,3])],
	[fig.add_subplot(gs[2:4,2]), fig.add_subplot(gs[2:4,3])],
	]


	for i,(outer_name,outer_fn) in enumerate({"MAX":alphaMax85, "AVG":alphaMean85}.items()):
		for j,(inner_name,inner_fn) in enumerate({"MAX":np.max, "AVG":np.mean}.items()):
		
			infl = {}
			for n in G.nodes():
				if n == target: infl[n] = 0
				infl[n] = influence(G, target, n, harm, outer_agg=outer_fn, inner_agg=inner_fn, path_counting="all", direction='in' )

			im1 = nx.draw_networkx_nodes(G, pos, ax=ax[i][j], edgecolors='k', linewidths=3, node_size=1500, cmap='PRGn', vmin=-20, vmax=20, nodelist=range(len(G.nodes)), node_color=[infl[n] for n in range(len(G.nodes))])
			nx.draw_networkx_edges(G, pos, ax=ax[i][j], width=3, node_size=1500, arrowsize=10)
			nx.draw_networkx_labels(G, pos, ax=ax[i][j], font_size=20, font_weight='bold', labels={ i:'{}'.format( round(h) ) for i,h in infl.items()} )
			ax[i][j].set_title(r'$I_{' + outer_name + ',' + inner_name + '}$')
	

	norm = mpl.colors.Normalize(vmin=-20, vmax=20)
	sm = mpl.cm.ScalarMappable(cmap="PRGn", norm=norm)
	sm.set_array([]) 
	cax = fig.add_subplot(gs[4, 2:])
	fig.colorbar(sm, cax=cax, orientation="horizontal")


	plt.show()
