# CausalPowerAnalysis

Code to perform causal power analysis from the [Kummerfeld, Williams, and Ma (2023) paper](https://link.springer.com/article/10.1007/s41060-023-00399-4.)

We created a set of generating causal graphs, and used them to generate statisticly normal data,
then tested the pc algorithm to determine the success rates in finding correct links in the correct direction.

We also assigned a random seed to each generating graph, so that each run with a given graph would use the same data.

## Single Runs

The easiest way is to create an  instance of the StructuralEquationDagModel class, found in picause.py.
```
In [1]: from picause import StructuralEquationDagModel

In [2]: sem = StructuralEquationDagModel(num_var=15, num_edges=27)
```

By default, sem now contains a randomly-generated causal graph with a uniform effect size of 0.1.
  In order to change the effect size, add the parameter beta = (the _square root_ of the desired effect size).
  
### Graph Integrity

So far there is no guarantee that the generated graph meets the desired constraints, which in our simulation were that
  each node would have a minimum independent random error of variance 0.1.
  
In order to test if that condition is violated, use the command:
```
In [3]: sem.test_residual_overflow()
Out[3]: False
```

In this case False means that the graph meets the conditions.
If True, then create additional instances of StructuralEquationDagModel until successful.


### 

## Batch Runs

When conducting a much larger number of runs, try using the discovery.py file.
 This method allows for greater parallelization, and testing various prameters on the same, pre-created generating graphs.

`python discover.py <nodes> <r> <graphnum> <graph> <seed> <index>`

where 
+ *nodes* is the number of nodes in the dataset.  
  This number can be larger than the number of nodes that appear in the graph string,  
  but it shouldn't be less.
+ *r* is the effect size between nodes  
  The effect size in this study was the same between each connected pair.
+ *graphnum* is an identifier for the number of the graph  
  It will be remembered in the output, in case you want to analyze which graphs give your discover algorithm  
  the hardest time of it.
+ *graph* specifies the generating graph  
   it is given as a  string in the form "a --> b, b --> c " giving the names of the nodes and the causal direction between them.
   we created our graphs randomly, testing for various quality criteria; sometimes finding a sucessful graph happened quickly, sometimes not-at-all quickly.  
   This caused havok for estimating time requests to the supercomputer, so we created the graphs in a seperate, prior step.   
   Brian Andrews is doing some interesting work on automating graph generation. Look for it soon in your favorite journals.  
   In the meanwhile, look the section graph generation (below)
+ *seed* is a random seed  
   Storing 500 huge datasets would have required terabytes of disc space.  
   Instead we assigned a seed number to each graph, and used it to generate the data upon request.  
   Then if a job was interrupted, we could restart at the point of interruption instead of having 
   to rerun everything on fresh data.
+ *index* is the directory number.  
   It specifies the name of the directory to use  
   The form of the name is 'dirx' for x is the index above.
   This directory will contain the job output. 
   Using multiple directories allowed for running multiple directories at the whim of the supercomputer's  
   scheduler, allowed for finer grained monitoring of job completion, and gave a place to seperate java config files.

## Output

discover.py will output to the directory specified by *index* (see above) a csv detailing, for each run:
* runtime
* truegraphid
* nodes
* edges
* metaparameter {sent to the causal discovery algorithm}
* r {the effect size}
* samples
* skeletal_TP {skeletal means edges found without regard to direction. TP is true positives}
* skeletal_FP
* skeletal_FN
* skeletal_TN
* oriented_TP {oriented means edges found and oriented correctly. See the paper for details}
* oriented_FP
* oriented_FN
* algorithm
