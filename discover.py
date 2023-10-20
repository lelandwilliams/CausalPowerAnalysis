import argparse
import os
import pandas
import platform
import picause
import time
from dataclasses import dataclass


@dataclass
class argsClass:
    """ This class to take the place of  command line
    args for testing purposes """
    nodes: int
    r: int
    graphnum: int
    graph: str
    seed: int
    index: int
    verbose: bool = False
    samples: int = 0
    meta: float = -1.0
    algorithm: str = ''


def args2argsClass(args=None):
    if args is None:
        args = process_args()

    return argsClass(args.nodes, args.r, args.graphnum, args.graphstr,
                     args.seed, args.index, args.verbose)


def process_args():
    """ uses argparse to obtain command line arguements
    when file is run as an executeable """
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes", help="Number of Nodes", type=int)
    parser.add_argument("r", help="Independent Error", type=float)
    parser.add_argument("graphnum", help="ID number of graph", type=int)
    parser.add_argument("graphstr", help="Graph String", type=str)
    parser.add_argument("seed", help="Random Seed", type=int)
    parser.add_argument("index", help='Index of Graph', type=int)
    parser.add_argument("-v", '--verbose', action="store_true")
    args = parser.parse_args()
    if args.verbose:
        print(args)
    return args


def row2args(row):
    """ Only used for retesting older results """
    return argsClass(nodes=row.nodes, r=row.r, graphnum=row.graphnum,
                     graph=row.graphstr, seed=int(row.seed),
                     samples=row.samples, algorithm=row.algorithm)


def graphrow2args(row):
    """ Creates an argsClass for a row in a truegraph dataframe.
    Used mostly for unit testing """
    return argsClass(nodes=row.vars, r=row.r, graphnum=row.graphnum,
                     graph=row.graphstr, seed=int(row.seed))


def causal_output_to_arrowstr(fname):
    """ reads output from causal-cmd,
    extracts the discovered graph info, and returns it as an arrow string"""
    with open(fname) as f:
        dgf = f.read()
    dg_edge_index = dgf.split('\n').index('Graph Edges:')
    dg_raw = dgf.split('\n')[dg_edge_index + 1:]
    dg_less_raw = [x.split('.')[1].strip() for x in dg_raw if ' --' in x]
    discovered_graph = ', '.join(dg_less_raw)

    return discovered_graph


def evaluate_discovery(discovery_file, args):

    truegraph_pl = picause.adjacencystr2pairlist(args.graph)
    truegraph_as = picause.adjacencystr2arrowstr(args.graph)

    discovered_graph = causal_output_to_arrowstr(discovery_file)
    if args.verbose:
        print('discovered graph:\n', discovered_graph)
    dg_pl = picause.arrowstr2pairlist(discovered_graph)

    #   create the results directory
    results = dict()
    results['truegraphid'] = [args.graphnum]
    results['nodes'] = [args.nodes]
    results['edges'] = [len(truegraph_pl)]
    results['r'] = [args.r]

    # +-----------------------------------------------+
    # |assess the discovered graph and save results |
    # +-----------------------------------------------+

    skeletal_matrix = picause.confusion_matrix(args.nodes,
                                               truegraph_pl,
                                               dg_pl)
    if args.verbose:
        print('skeletal matrix:\n', skeletal_matrix)

    oriented_matrix = picause.oriented_confusion_matrix(truegraph_as,
                                                        discovered_graph,
                                                        verbose=args.verbose)
    for k, v in oriented_matrix.items():
        results[k] = v

    results['skeletal_TP'] = [skeletal_matrix[0]]
    results['skeletal_FP'] = [skeletal_matrix[1]]
    results['skeletal_FN'] = [skeletal_matrix[2]]
    results['skeletal_TN'] = [skeletal_matrix[3]]

    results['discovered_directed_edges'] = \
        picause.arrowstr2adjacencystr(discovered_graph, directed=True)
    results['discovered_undirected_edges'] = \
        picause.arrowstr2adjacencystr(discovered_graph, directed=False)

#   if args.verbose: print(pandas.DataFrame(results))

    return pandas.DataFrame(results)


def discover(args):
    sample_sizes = [50, 100, 200, 400, 800, 1600, 3200, 6400]
    sample_sizes += [12800, 25600, 51200, 102400]
    if args.samples > 0:
        sample_sizes = [args.samples]
    numrows = max(sample_sizes)

    # |   Set Home Directory and Java Directory
    if "CentOS" in platform.freedesktop_os_release()['NAME']:
        basedir = "/home/erichk/will4379/"
    else:
        basedir = "/home/lhw/"

    # |   Create a directory space for the data files,
    # |   results files, and jvm system files
    jvm_dirname = basedir + "JavaDirs/dir{}".format(args.index)
    systemprefsdir = jvm_dirname + "/.systemPrefs"
    os.makedirs(systemprefsdir, exist_ok=True)
    discovery_prefix = 'results'
    # determine filename of output of causal-cmd
    discovery_file = jvm_dirname + '/' + discovery_prefix + '.txt'

    # |   Set Truegraph
    edges = picause.adjacencystr2pairlist(args.graph)

    # |             Create SEM object
    SEM = picause.StructuralEquationDagModel(num_var=args.nodes,
                                             E=edges,
                                             beta=args.r,
                                             make_model=True,
                                             seed=args.seed)
    if args.verbose:
        print(SEM)

    # Have the SEM class generate data from a given seed
    data = SEM.generate_data(num_data_points=numrows)
    if args.verbose:
        print(data.head())
    results_list = list()

    for samples in sample_sizes:

        datafile = jvm_dirname + '/data.csv'
        data[:samples].to_csv(datafile, index=False)
        algorithms = ['pc', 'fges', 'grasp']
        if args.algorithm != "":
            algorithms = [args.algorithm]
        for algorithm in algorithms:
            metas = [0.001, 0.01, .05, 0.1]
            if args.meta >= 0:
                metas = [args.meta]
            elif algorithm != 'pc':
                metas = [2]
            for meta in metas:
                begin_time = time.time()
                causal_output = picause.discovery_results(sem=SEM,
                                                          datafile=datafile,
                                                          jdir=jvm_dirname,
                                                          meta=meta,
                                                          write=False,
                                                          algorithm=algorithm,
                                                          output_directory=jvm_dirname,
                                                          output_prefix=discovery_prefix)
                if args.verbose:
                    print("Causal output\t\n", causal_output, "\n")
                runtime = time.time() - begin_time
                run_results = evaluate_discovery(discovery_file, args)
                run_results['runtime'] = ["{:.2f}".format(runtime)]
                run_results['metaparameter'] = [meta]
                run_results['samples'] = [samples]
                run_results['algorithm'] = [algorithm]
                if args.verbose:
                    print(pandas.DataFrame(run_results))
                results_list.append(run_results)
    results = pandas.concat(results_list, ignore_index=True)
    results.to_csv(jvm_dirname + '/results.gz.csv',
                   index=False,
                   compression='gzip')
    os.remove(jvm_dirname + '/data.csv')

    # Create filename to signal that entire job completed successfully
    with open(jvm_dirname + '/COMPLETE', 'w') as f:
        f.write("")

    return results


if __name__ == "__main__":
    #   args = process_args()
    args = args2argsClass()
    discover(args)
