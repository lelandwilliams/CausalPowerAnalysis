import pandas
import numpy

rfile = '~/SimDec22Summary/master_results.csv.gz'
df = pandas.read_csv(rfile, compression='gzip')
df.rename(columns={'skeletal_TP': 'adjacency_TP',
                   'skeletal_FN': 'adjacency_FN',
                   'skeletal_FP': 'adjacency_FP',
                   'skeletal_TN': 'adjacency_TN'}, inplace=True)

df['oriented_precision'] = df.oriented_TP / (df.oriented_TP + df.oriented_FP)
df['oriented_sensitivity'] = df.oriented_TP / (df.oriented_TP + df.oriented_FN)
df['adjacency_precision'] = df.adjacency_TP / (df.adjacency_TP + df.adjacency_FP)
df['adjacency_sensitivity'] = df.adjacency_TP / (df.adjacency_TP + df.adjacency_FN)
df['adjacency_specificity'] = df.adjacency_TN / (df.adjacency_TN + df.adjacency_FP)

result_cols = ['nodes', 'edges', 'metaparameter', 'r',
               'samples', 'nruns', 'mean_runtime', 'algorithm']
results = {x: [] for x in result_cols}

for c in ['oriented_TP', 'oriented_FP', 'oriented_FN', 'oriented_precision',
          'oriented_sensitivity', 'adjacency_TP', 'adjacency_FP',
          'adjacency_FN', 'adjacency_TN', 'adjacency_precision',
          'adjacency_sensitivity', 'adjacency_specificity']:
    for m in ['low', 'mean', 'high']:
        results["{}_{}".format(m, c)] = []

vc = df[['nodes', 'edges', 'samples', 'r', 'metaparameter', 'algorithm']].value_counts()
for t in vc.index:
#   param_cols = ['nodes', 'edges', 'samples', 'r', 'metaparameter', 'algorithm']
    nodes, edges, samples, r, meta, algorithm = t
    results['nodes'].append(nodes)
    results['edges'].append(edges)
    results['samples'].append(samples)
    results['r'].append(r)
    results['metaparameter'].append(meta)
    results['algorithm'].append(algorithm)
    results['nruns'].append(500)

    subdf = df.loc[(df.nodes == nodes) & (df.edges == edges) &
                   (df.metaparameter == meta) & (df.r == r) &
                   (df.samples == samples) & df.algorithm == algorithm]

    results['mean_runtime'].append(round(subdf['runtime'].mean(), 3))
    for c in ['oriented_TP', 'oriented_FP', 'oriented_FN',
              'oriented_precision', 'oriented_sensitivity',
              'adjacency_TP', 'adjacency_FP', 'adjacency_FN',
              'adjacency_TN', 'adjacency_precision',
              'adjacency_sensitivity', 'adjacency_specificity']:
        alpha_idx = int(round(len(subdf) * 0.025, 0))
        if subdf[c].count() > alpha_idx:
            val_list = subdf[c].sort_values(na_position='first', ascending=True).round(3)
            val_list.reset_index(inplace=True)

            valname = 'low_{}'.format(c)
            val = val_list[alpha_idx]
            results[valname].append(val)

            valname = 'high_{}'.format(c)
            val = val_list[val_list.index.max() - alpha_idx]
            results[valname].append(val)

            valname = 'mean_{}'.format(c)
            val = round(val_list.mean(), 3)
            results[valname].append(val)
resultsdf = pandas.DataFrame(results)
