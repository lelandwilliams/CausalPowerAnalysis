import os
import pandas
from shutil import rmtree
import time


def jobrunner():
    # * define filenames and other constants
    homedir = '/home/erichk/will4379/'
    simdir = homedir + 'SimDec22Summary/'
    jobstatus = simdir + 'jobstatus.csv.gz'
    javatopdir = homedir + 'JavaDirs/'
    resultsfile = 'results7.csv.gz'
    start_time = time.time()
    max_jobs = 1000
    max_collate_time = 1800 # time in seconds to work on collating
    max_jobstart_time = 2100 # time in seconds at which no more jobs will be created

    # * load job dataframe
    jobs = pandas.read_csv(jobstatus)

    if "JavaDirs" not in os.listdir(homedir):
        os.mkdir(javatopdir)

    num_jobs_remaining = len(jobs[jobs.Status == "Unstarted"])
    num_jobs_untabulated = len(os.listdir(javatopdir))

    # * Schedule a new copy of self if necessary
    if num_jobs_remaining > 0 or num_jobs_untabulated > 0:
        s = "sbatch << EOF\n"
        s += "#!/bin/bash -l\n "
        s += "#SBATCH -A erichk\n"
        s += "#SBATCH --begin=now+1hour\n"
        s += "#SBATCH --time=45:00\n"
        s += "#SBATCH --mem=1g\n"
        s += "#SBATCH --ntasks=1\n"
        s += "#SBATCH --mail-type=NONE\n"
        s += "#SBATCH --error=slurmoutput/jobrunner.err\n"
        s += "#SBATCH --job-name=jobrunner\n"
        s += "#SBATCH --output=slurmoutput/jobrunner.txt\n"
        s += "python3 jobrunner.py\n"
        s += "EOF\n"

        _ = os.popen(s).read()

    # * Examine existing job directories, collate them if they contain finished jobs.
    for javadir in os.listdir(javatopdir):
        if time.time() - start_time > max_collate_time:
            break
        localdir = javatopdir + javadir + '/'
        dirnum = int(javadir[3:])
        if 'COMPLETE' in os.listdir(localdir):
            # read in results and save them with exisiting results
            newresults = pandas.read_csv(localdir + 'results.gz.csv', compression='gzip')
            if resultsfile not in os.listdir(simdir): 
                newresults.to_csv(simdir + resultsfile, index=False,
                                  compression='gzip')
            else:
                results = pandas.read_csv(simdir + resultsfile, compression='gzip')
                combined_results = pandas.concat([results, newresults], ignore_index=True)
                combined_results.to_csv(simdir + resultsfile, index=False,
                                        compression='gzip')

            # update job dataframe to show job has finished
            jobs.at[dirnum, 'Status'] = "Completed"
            jobs.to_csv(jobstatus, index=False, compression='gzip')
            # wipe directory (or add to wipe list)
            rmtree(localdir)

    # * Create new jobs, if necessary
    num_todo = min(max_jobs, num_jobs_remaining)
    for i in range(num_todo):
        if time.time() - start_time > max_jobstart_time:
            break
        # choose an unstarted job
        jobidx = jobs[jobs.Status == "Unstarted"].index.min()
        # create java directory
        localdir = javatopdir + 'dir{}/'.format(jobidx)
        os.mkdir(localdir)
        # mark job as 'pending'
        jobs.at[jobidx, 'Status'] = 'Pending'
        # save job dataframe
        jobs.to_csv(jobstatus, index=False, compression='gzip')
        # create job to run graph
        row = jobs.loc[jobidx]
        bash_graphstr = row.graphstr.replace(';', '\;')
        s = "sbatch << EOF\n"
        s += "#!/bin/bash -l\n "
        s += "#SBATCH -A erichk\n"
        s += "#SBATCH --time=10:00:00\n"
        s += "#SBATCH --mem=4g\n"
        s += "#SBATCH --ntasks=1\n"
        s += "#SBATCH --mail-type=NONE\n"
        s += "#SBATCH --error={}slurm.err\n".format(localdir)
        s += "#SBATCH --job-name=job{}\n".format(jobidx)
        s += "#SBATCH --output={}joboutput.txt\n".format(localdir)
        s += 'python3 discover.py {} {} {} {} {} {}\n'.format(row.vars,
                                                              row.r,
                                                              row.graphnum,
                                                              bash_graphstr,
                                                              row.seed,
                                                              jobidx)
        s += "EOF\n"

        _ = os.popen(s).read()



if __name__ == "__main__":
    jobrunner()
