import os
import sys
from itertools import chain

# +--------------------------------------+
# |     Establish Subdirectory Names     |
# +--------------------------------------+
simname = 'SimDataDec22'
#basedir = '/home/lhw/'
#if 'Red Hat' in sys.version:
basedir = '/home/erichk/will4379/'
graphdir = basedir + simname + '/truegraphs/'
#esultsdir = basedir + simname + '/csv/' + 'lowsamples/'
resultsdir = basedir + simname + 'lowsamples/'
#os.makedirs(graphdir, exist_ok=True)
#os.makedirs(resultsdir, exist_ok=True)


gstr = "graph-{}-vars_{}-edges_{}-r_{}.txt"
dstr = 'results_{}-vars_{}-edges_{}-r_{}-meta_{}-graphnum-{}_{}-samples.csv'

nodes = [10, 20, 40, 100]
densities = [1, 1.5, 2]
rs = [0.1, 0.3, 0.5]
samples = [50, 100, 200, 400, 800, 1600, 3200, 6400]
#samples = [12800, 25600, 51200, 102400]
alphas = [0.001, 0.01, .05, 0.1]
graphnums = range(1, 501)

pcqueue = ((n, int(n * density), r, graph, 'pc', sample, alpha) for n in nodes \
        for density in densities \
        for r in rs \
        for graph in graphnums \
        for sample in samples \
        for alpha in alphas)

othqueue = ((n, int(n * density), r, graph, algorithm, sample, 2) for n in nodes \
        for density in densities \
        for r in rs \
        for graph in graphnums \
        for algorithm in ['grasp', 'fges'] \
        for sample in samples)

jobnum = 0
i = 0
i_written = False
start_index = 0

for num_v, num_edges, r, graph, algorithm, nsamples, alpha in chain(pcqueue, othqueue):
    graphfname = gstr.format(num_v, num_edges, r, graph)
    outputfname = dstr.format(num_v, num_edges, r, alpha, algorithm, graph, nsamples)

    # high density/ high-r graphs are hard to generate, so ignore for now
    if r == 0.5 and (num_edges / num_v == 2):
        print('High R and Density, SKIPPING:', outputfname)
        continue

    # don't bother if the generating graph doesn't exist
    if not os.path.isfile(graphdir + graphfname):
        print('Graph file does not exist:', graphfname)
        continue

    # in case of restart, skip the first start_index combinations that have already been done
    if i  < start_index:
        i += 1
        continue

    # Double checking that results haven't already been obtained for this combo 
    if os.path.isfile(resultsdir + outputfname):
        i += 1
        print('Results exist, SKIPPING:', outputfname)
        continue

    # If this is the first job to run, save it's index number and use that to restart the job next time
    if not i_written:
        print(i)
        with open('StartIndex.txt', 'w') as f:
            f.write(str(i))
            i_written = True

    print('RUNNING', outputfname)
    s = "sbatch << EOF\n"
    s += "#!/bin/bash -l\n"        

    if algorithm == 'pc':
        s += "#SBATCH --time=1\n"
        s += "#SBATCH --mem=1g\n"
    else:
        s += "#SBATCH --time=20\n"
        s += "#SBATCH --mem=4g\n"

    s += "#SBATCH --ntasks=1\n"
    s += "#SBATCH --mail-type=NONE\n"
    s += "#SBATCH --error=slurmoutput/slurm-{}_{}_{}_{}_{}_{}_{}_{}.err\n".format(num_v, num_edges, r, graph, algorithm, nsamples, alpha, jobnum)
    s += "#SBATCH --job-name={}\n".format(algorithm)
    s += "#SBATCH --output=slurmoutput/joboutput.txt\n"
    s += "srun python3 discover.py {} {} {} {} {} {} {} {}\n".format(num_v, num_edges, r, graph, algorithm, nsamples, alpha, jobnum)
    s += "EOF\n"

    _ = os.popen(s).read()
    jobnum +=1
#   break

