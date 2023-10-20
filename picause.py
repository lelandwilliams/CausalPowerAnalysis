"""
picause:
"""

import math
import numpy
import os
import pandas
import platform
import random
import sys
import time
import textwrap


def adjacencystr2arrowstr(adjacencystr, directed=True):
    astr = '-->'
    if not directed:
        astr = '---'
    s = ""

    for l in adjacencystr.split(';'):
        if len(l) == 0:
            continue
        hexstrs = textwrap.wrap(l, 2)
        source = "x_{}".format(int("0x"+hexstrs[0], 0))
        for h in hexstrs[1:]:
            dest = "x_{}".format(int("0x"+h, 0))
            s += "{} {} {}, ".format(source, astr, dest)
    return s[:-2]


def adjacencystr2pairlist(adjacencystr):
    arrowstr = adjacencystr2arrowstr(adjacencystr)
    return arrowstr2pairlist(arrowstr)


def arrowstr2adjacencystr(arrowstr, directed=True):
    """
    Takes an arrow string, in the form of u1 --> v1, u2 --- v2, ...
    and turns it into an adjaceny string, in the form of xxyyzz;aabbcc...
    where xx and aa are sources, and yy and zz (etc) are the destinations
    and xx and yy are two-hexdigit numbers
    the semicolon is the delimiter between adjacencylines

    parameters:
    ----------
       arrowstr: a string of directed or undirected edges
       directed: a boolean to determine whether to include only
           directed edges or only undirected edges.
           The intension is to make it possible to have seperate strings
           for directed and undirected edges.
    """

    d = arrowstr2adjacencydict(arrowstr, directed)
    s = ""

    for key in d:
        hex_source = "{:02X}".format(int(key[2:]))
        s += hex_source
        for val in d[key]:
            hex_target = "{:02X}".format(int(val[2:]))
            s += hex_target
        s += ';'
    return s


def arrowstr2adjacencydict(arrowstr, directed=True):
    """
    Takes an arrow string, in the form of u1 --> v1, u2 --- v2, ...
    and returns a dictionary, with keys the source, and values a list of
    each source's targets

    parameters:
    ----------
       arrowstr: a string of directed or undirected edges
       directed: a boolean to determine whether to include only
           directed edges or only undirected edges.
    """

    d = dict()
    astr = '-->'
    if not directed: astr = '---'

    for pair in arrowstr.split(','):
        if astr not in pair:
            continue
        u, _, v = pair.strip().split()
        if u not in d: d[u] = []
        d[u].append(v)
    return d


def arrowstr2pairlist(s):
    """ takes a string of edges in Tetrad's format and
    return a list of edge pairs"""
    if len(s) == 0:
        return []
    s = s.strip()
    if s[-1] == ',':
        s = s[:-1]
    if len(s.split()) == 0:
        return []
    if len(s.split()) == 1:  # handles the case that there is only one pair,
                             # in which case there is no comma, which would
                             # cause errors in the final case.
        return (s.split()[0], s.split()[2])
    return [(x.split()[0], x.split()[2]) for x in s.split(',')]


def pairlist2arrowstr(E, human_readable=False):
    """ obtain an string of directed edges from an interable of vertice pairs
        it assumes that a pair (u,v) denotes a directed edge from u to v.

    params:
    ______
        E: an iterable containing (u,v) pairs
        human_readable: a flag that controls the style of the output

    output:
    _______
        a Tetrad style u --->v string """
    if human_readable:
        s = ""
        count = 0
        for u, v in E:
            s += "\t{} --> {}".format(u, v)
            count += 1
            if count % 5 == 0:
                s += "\n"
        return s
    else:
        s = ""
        for u, v in E:
            s += "{} --> {}, ".format(u, v)
        return s[:-1]


def discover(df_filename, o_filename, jdir=None, meta=0.1, algorithm='pc',
             output_directory=None, verbose=False):
    # Determine directory location of jar file
    if "CentOS" in platform.freedesktop_os_release()['NAME']:
        basedir = "/home/erichk/will4379/Picause/"
    elif 'Projects' in os.listdir('/home/lhw'):
        basedir = "/home/lhw/Projects/Picause/"
    elif 'Work' in os.listdir('/home/lhw'):
        basedir = "/home/lhw/Work/Picause/"
    elif 'Picause' in os.listdir('/home/lhw'):
        basedir = "/home/lhw/Picause/"
    else:
        raise RuntimeError('Cannot find jar file')

    javajar = 'causal-cmd-1.4.1-SNAPSHOT-jar-with-dependencies.jar'

    # Create directories to contain JVM settings files
    if jdir is None:
        java_base_cmd = 'java -jar ' + basedir + javajar
    else:
        dir_opt = "-Djava.util.prefs.userRoot={} -Djava.util.prefs.systemRoot={}".format(jdir,jdir)
        java_base_cmd = 'java ' + dir_opt + ' -jar ' + basedir + javajar

    # Build options to send to causal-cmd
    java_opts = " --algorithm {} ".format(algorithm)
    java_opts += " --data-type continuous"
    java_opts += " --dataset {}".format(df_filename)
    java_opts += " --delimiter comma "
    java_opts += " --prefix {} ".format(o_filename)

    # Add options specific to each algorithm
    if algorithm == 'grasp':
        java_opts += " --test fisher-z-test "
        java_opts += " --cacheScores true "
        java_opts += " --graspDepth 3"
        java_opts += " --score sem-bic-score"
        java_opts += " --penaltyDiscount {}".format(meta)
    elif algorithm == 'pc':
        java_opts += " --alpha {}".format(meta)
        java_opts += " --test fisher-z-test "
    else:
        java_opts += "--score sem-bic-score"
        java_opts += " --penaltyDiscount {}".format(meta)

    # Specifies directory where output file is to be placed
    if output_directory is None:
        java_opts += " --out {}".format(jdir)
    else:
        java_opts += " --out {}".format(output_directory)

    java_cmd = java_base_cmd + java_opts
    if verbose:
        print(java_cmd)
    pid = os.popen(java_cmd)
    java_output = pid.read()
    pid.close()

    return java_output

def discovery_results(sem, datafile, jdir=None, meta=0.1, dgraphfile="", write=True, algorithm='pc', output_directory=None, output_prefix=None):
    """
    runs a causal discovery algorithm on a datafile, saves the discovered graph, and returns a confusion matrix
    
    parameters:
    ----------
        sem: a picause.StructuredEquationDagModel class
            ** Warning, sem actually does nothing and is to be removed **
        datafile: the csv file containing the observations from which graphs are inferred
        jdir: the directory the jvm should use for its userPrefs file
        meta: the metaparameter relavant to the specified algorithm
        dgraphfile: the file the discovered graph should be saved under
        write: whether or not the algorithm should save the discovered graph
        algorithm: which algorithm to ask discover() to use
        output_directory: the path to the directory where the output file shall be placed
        output_prefix: the name of the output file (not including the .txt)

    returns:
    --------
        the discovered graph in arrow-string format
    """

    if output_prefix is None:
        output_prefix = "results"
    outfile = "{}/{}.txt".format(output_directory, output_prefix)
    print(outfile)
    # run the discovery algorithm
    data = discover(datafile, output_prefix, jdir=jdir, meta=meta, algorithm=algorithm, output_directory=output_directory)
#   print(data)
    with open(outfile, 'r') as f:
        results = f.readlines()
    results_s = ""
    for r in results[results.index('Graph Edges:\n') + 1:]:
        if '-->' not in r:
            continue
        results_s += r.split(". ")[1][:-1] + ', '
    results_s = results_s[:-2]
    if write:
        with open(dgraphfile, 'w') as f:
            f.write(results_s)
#   discovered_graph = arrowstr2pairlist(results_s)
#   return confusion_matrix(len(sem.V), sem.E, discovered_graph)
    return results_s


def oriented_confusion_matrix(tg, dg, retval="dict", verbose=False):
    """
    parameters:
    __________
        tg: an arrow string of edges representing the true graph
        dg: a string of edges representing the discovered graph
        retval: which to return, a dictionary of the scores, or the edges
    """

    if type(tg) != str:
        raise ValueError('tg must be a string')
    if len(tg) > 0 and "-->" not in tg and "---" not in tg:
        raise ValueError('tg must be an arrow string')
    if len(dg) > 0 and "-->" not in dg and "---" not in dg:
        raise ValueError('dg must be an arrow string')
    if type(dg) != str:
        raise ValueError('dg must be a string')
    if retval not in ["tuple", "dict", "edges"]:
        raise ValueError('retval only takes values {tuple, edges}')

    # make true_edges into a list
    true_edges = set(arrowstr2pairlist(tg))
    if verbose:
        print("\n-- Oriented Confusion Matrix --")
        print("True Edges:\t\t\t", true_edges)

    # break down discovered graph into lists of directed and undirected
    discovered_de = list()
    discovered_ue = list()
    if len(dg) > 0:
        for edge in [x for x in dg.split(',')]:
            u, d, v = edge.split()
            if d == '---':
                discovered_ue.append((u, v))
            if d == '-->':
                discovered_de.append((u, v))

    if verbose:
        print("Discovered directed edges:\t", discovered_de)
        print("Discovered undirected edges:\t", discovered_ue)

    d = {x: [] for x in ['TP', 'FP', 'FN']}

    for e in true_edges:
        rev_e = tuple(reversed(e))
        if e in discovered_de:
            d['TP'].append(e)
        elif rev_e in discovered_de:
            d['FP'].append(rev_e)
            d['FN'].append(e)
        elif e in discovered_ue:
            d['FN'].append(e)
        elif rev_e in discovered_ue:
            d['FN'].append(e)

    if verbose:
        print("True Positive edges:\n\t", d['TP'])
        print("False Positive edges:\n\t", d['FP'])
        print("False Negative edges:\n\t", d['FN'])
        print("--------------------\n\n")

    results = {'oriented_TP': len(d['TP'])}
    results['oriented_FP'] = len(d['FP'])
    results['oriented_FN'] = len(d['FN'])

    if retval == 'tuple' or retval == 'dict':
        return results
    else:
        return d


def confusion_matrix(num_nodes, true_e, test_e):
    true_positives = []

    M = [0] * 4
    generating_e = true_e.copy()
    discovered_e = test_e.copy()

    for u, v in discovered_e:
        if (u, v) in generating_e:
            true_positives.append((u, v))
            generating_e.remove((u, v))
        elif (v, u) in generating_e:
            true_positives.append((u, v))
            generating_e.remove((v, u))
    for e in true_positives:
        discovered_e.remove(e)

    M[0] = len(true_positives)
    M[1] = len(discovered_e)
    M[2] = len(generating_e)
    M[3] = (num_nodes * (num_nodes-1) // 2) - sum(M)

    return tuple(M)

def int2pairlist(i, len_V):
    if len_V == 20:
        M = numpy.array(list(format(bin(i), "0400b")),dtype=numpy.uint8).reshape(20,20)
    elif len_V == 40:
#       M = numpy.array(list(format(bin(i), "01600b")),dtype=numpy.uint8).reshape(40,40)
        M = numpy.array(list(format(bin(i), "01600b")),dtype=numpy.uint8).reshape(40,40)
    E = []
    for i in range(len_V):
        for j in range(len_V):
            if M[i][j] == 1:
                E.append("x_{}".format(i+1),"x_{}".format(y+1))
    return E


class Model:
    def __init__(self, num_var=None, V=None, E=None, seed=None, num_edges=None):
        self.seed = seed
        self.E = E
        self.V = V
        
        if self.seed is None:
            self.seed = int(os.urandom(sys.getsizeof(int())).hex(), 16)
        self.rng = numpy.random.default_rng(self.seed)
        
        if self.E is not None and self.V is None and num_var is None:
            self.V = sorted(set([v for x in E for v in x]))
        if self.V is None:
            self.V = ["x_{}".format(i) for i in range(1, num_var + 1)]

class StructuralEquationDagModel(Model):
    def __init__(self, num_var=None, V=None, E=None, seed=None, num_edges=None, make_model=True, beta=math.sqrt(0.1)):
        super().__init__(num_var=num_var, V=V, E=E, seed=seed, num_edges=num_edges)
        if self.E is None and not self.V is None:
            self.E = self.make_random_graph(self.V, rng=self.rng, num_edges=num_edges)
            
        if make_model:
            self.make_implied_model(beta=beta)
            
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        s = "Structural Equation DAG Model\n"
        s += "{} Vertices and {} Edges\n".format(len(self.V), len(self.E))
        s += "Seed: {}\n".format(self.seed)
        s += "Vertices:\n"
        s += str(self.V)
        s += "\n\n"
        s += "Edges:\n" 
        s += pairlist2arrowstr(self.E, human_readable=True)
        s += "\nTopological Order:\n\t"
        s += self.get_topological_order(as_string=True)
        s += "\nModel:\n\t:"
        s += self.get_model_str()
        return s
   
    def set_E(self, new_E):
        self.E = new_E
        self.num_edges = len(new_E)
        self.make_sem_im()
        
    def get_model_str(self):
        s = ""
        for var in self.get_topological_order():
            s += "{} = ".format(var)
            for parent, coef in self.model[var].items():
                s += "({:1.3f}) {} + ".format(coef, parent)
            s += "({:1.3f})e\n".format(self.residual[var])
        return s
                
    def generate_data(self, num_data_points=100):
        df = pandas.DataFrame()
        for var in self.residual:
            df[var] = self.rng.normal(0, math.sqrt(self.residual[var]), num_data_points)
            for parent in self.model[var]:
                df[var] += self.model[var][parent] * df[parent]
        return df[self.V]
        
   
    def get_topological_order(self, model=None, as_string=False):
        """
        Using the parent info in the model, determine the 'topological' order of the nodes.
        A Topolocial ordering is a (potentially nonunique) ordering where no later node
        can be a parent of an earlier node.
        """
        if model is None:
            model = self.model
        var_order = []
        remaining_vars = list(model.keys())
        while len(remaining_vars) > 0:
            for v in remaining_vars:
                ready_flag = True
                for parent in model[v].keys():
                    ready_flag &= (parent in var_order)
                if ready_flag:
                    var_order.append(v)
            for v in var_order:
                if v in remaining_vars:
                    remaining_vars.remove(v)
                    
        if as_string:
            s = ""
            for v in var_order:
                s += v
                if var_order.index(v) < len(var_order) -1:
                    s += " < "
            return s
        else:
            return var_order
    
    def make_cov_matrix(self, verbose=False):
        variables = self.get_topological_order()
        cov_matrix = pandas.DataFrame(numpy.identity(len(self.V)), index=variables, columns=variables)

        for u in variables[1:]:
            parents_u = self.model[u]
            for prior_var in variables:
                if prior_var == u:
                    break
                else:
                    cov_sum = 0.0
                    for parent in parents_u:
                        cov_sum += self.model[u][parent] * cov_matrix[parent][prior_var]
                    cov_matrix[prior_var][u] = cov_sum
                    cov_matrix[u][prior_var] = cov_sum
        if verbose:
            print('Heres the implied covariance matrix:')
            print(cov_matrix)
            print()
        
        return cov_matrix
    
    def make_implied_model(self, beta):
        self.make_sem_im(beta=beta) #instantiates self.model
        self.implied_cov_matrix = self.make_cov_matrix()
        self.make_residuals(self.implied_cov_matrix)
        
    def make_residuals(self, M, verbose=True):
        """ 
        creates the class member residual, a dictionary of variables and their residual, or "leftover", or "free", variance
        """
        self.residual = {}
        variable_order = self.get_topological_order(self.model)
        for variable in variable_order:
            parents = list(self.model[variable].keys())
            parent_matrix = M.loc[parents, parents].copy()
            for parent in parents:
                parent_matrix.loc[parent, :] *= self.model[variable][parent]
                parent_matrix.loc[:, parent] *= self.model[variable][parent]
            self.residual[variable] = 1 - parent_matrix.sum().sum()
            
    def make_sem_pm(self):
        """
            creates the dicitonary data structure for a parametric model
            Does not assign edge weights
        """
        self.model = {v:{} for v in self.V}
        for parent, node in self.E:
            self.model[node][parent] = None

    def make_sem_im(self, beta=math.sqrt(0.1)):
        """ creates a sem with the specified beta assigned to all edges
            non-varying weight support to be added later
        """
        self.make_sem_pm()
#       sqrt_point_one = math.sqrt(0.1)
        for node, parents in self.model.items():
            for parent in parents.keys():
                self.model[node][parent] = beta
                
    def test_residual_overflow(self):
        return min(self.residual.values()) < 0
    
    def make_random_graph(self, V=None, avg_deg=2.0, num_edges=None, rng=None):
        
        """ Given a list of vertices, return a list of pairs representing a set of directed edges """
        if V is None:
            V = self.V
        if rng is None:
            rng = numpy.random.default_rng()
        V_canonical = V.copy()
        rng.shuffle(V_canonical)
        indegrees = {v:0 for v in V}
        if num_edges is None:
            num_edges = int(len(V) * avg_deg)
        
        graph_done = False
        while not graph_done:
            graph_done = True
            indegrees = {v:0 for v in V}
            possibles = []
            for i in range(0, len(V_canonical) -1):
                for j in range(i+1, len(V_canonical)):
                    possibles.append((V_canonical[i], V_canonical[j]))
            E = random.sample(possibles, num_edges)
            for u,v in E:
                indegrees[v] +=1
                if indegrees[v] > 9:
                    graph_done = False
                    
        return E


