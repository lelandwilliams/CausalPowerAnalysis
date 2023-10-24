# CausalPowerAnalysis

Code to perform causal power analysis from the [Kummerfeld, Williams, and Ma (2023) paper](https://link.springer.com/article/10.1007/s41060-023-00399-4.)

We created a set of generating causal graphs, and used them to generate statisticly normal data,
then tested the pc algorithm to determine the success rates in finding correct links in the correct direction.

We also assigned a random seed to each generating graph, so that each run with a given graph would use the same data.

## Basic Usage
In a simpler use case, you can test the strength of one run on a given generator graph by typing

`python discover.py <nodes> <r> <graphnum> <graph> <seed> <index>`

where 
+ *nodes* is the number of nodes in the dataset.  
  This number can be larger than the number of nodes that appear in the graph string,  
  but it shouldn't be less.
+ *r* is the effect size between nodes
+ *graphnum* is an identifier for the number of the graph
+ *graph* specifies the generating graph  
   it is given as a  string in the form "a --> b, b --> c " giving the names of the nodes and the causal direction between them.
   we created our graphs randomly, which sometimes happened quickly, sometimes not-at-all quickly.  
   This caused havok for estimating time requests to the supercomputer, so we made the graphs seperately.  
   Brian Andrews is doing some intersting work on automating graph generation. Look for it soon in your favorite journals.  
   In the meanwhile, graph supply is left as a exercise for the reader.
+ *seed* is a random seed  
   Storing 500 huge datasets would have required Terabytes of disc space.  
   Instead we assigned a seed number to each graph, and used it to generate the data upon request.  
   Then if a job was interrupted, we could restart at the point of interruption instead of having 
   to rerun everything on fresh data.
+ *index* is the directory number.  
   It specifies the name of the directory to use  
   The form of the name is 'dirx' for x is the index above.
   This directory will contain the job output. 
   Using multiple directories allowed for running multiple directories at the whim of the supercomputer's  
   scheduler, allowed for finer grained monitoring of job completion, and gave a place to seperate java config files.

## Explanation
We found that creating the graphs that satisfy our conditions (no incoming variance > 0.9) could be time consuming,
so we created the graphs first. We also specified a random seed used in generating the fake data from the graph.
