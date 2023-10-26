# CausalPowerAnalysis

Code to perform causal power analysis from the [Kummerfeld, Williams, and Ma (2023) paper](https://link.springer.com/article/10.1007/s41060-023-00399-4.).
  
Uses causal-cmd from the [Center for Causal Discovery](ccd.pitt.edu).

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

There is no guarantee that the graph generated when calling the StructuralEquationDagModel constructor meets the desired constraints, which in our simulation were that
  each node would have a minimum independent random error of variance 0.1.
  
In order to test if that condition is violated, use the command:
```
In [3]: sem.test_residual_overflow()
Out[3]: False
```

In this case False means that the graph meets our constraints.
  If True, then create additional instances of StructuralEquationDagModel until successful.

###  Generating Data

next create a Pandas dataframe with the desired number of observations, and save it.
  the index=False bit is important, else the index will become an additonal column in the csv and cause problems.
```
In [4]: df = sem.generate_data(102)

In [5]: df.head()
Out[5]: 
        x_1       x_2       x_3       x_4       x_5       x_6       x_7       x_8       x_9      x_10      x_11      x_12      x_13      x_14      x_15
0  1.088586 -0.276645  1.205388 -0.966795 -0.023381  1.807379  0.805810  1.133299  0.046535  0.188513  1.501350 -0.083047  1.674610 -0.905475  1.908718
1  0.054849 -0.975134  0.027781 -1.392744  0.639920 -0.885078  1.221120 -0.014736 -1.131883 -0.347999 -0.495118  1.052720 -1.997742  0.087143 -0.955062
2 -0.764739 -0.456137  1.515046  0.496463 -1.159423  0.046815 -0.228253 -0.182869  0.795919  0.178344  0.494876 -0.701653 -0.262900 -1.345451 -0.366615
3  0.276708  1.049682  0.127676  0.317868  0.838541 -0.800638  0.544702  0.860535  0.209727  0.664409  0.207855  0.139667 -0.056168  1.431515 -1.492470
4 -1.185480 -0.608734 -0.009538 -1.313906 -1.548134 -0.779098  0.378475 -0.840022  2.659831 -1.706559 -1.093263 -2.145179  0.749385 -0.354218  1.614622

In [6]: df.to_csv('my_data.csv', index=False)
```

### Graph discovery

Assuming that the causal-cmd jar is located within in the current working directory, a discovery algorithm can be run on the data like this:

```
In [6]: from pathlib import Path

In [7]: cwd = Path().absolute()

In [8]: from picause import  discovery_results

In [9]: results = discovery_results(sem, 'my_data.csv', output_directory=str(cwd), write=False)
Oct 26, 2023 5:19:49 PM java.util.prefs.FileSystemPreferences$6 run
WARNING: Prefs file removed in background /home/lhw/.java/.userPrefs/prefs.xml

In [10]: print(results)
x_1 --> x_8, x_10 --> x_5, x_10 --> x_8, x_11 --> x_4, x_12 --> x_5, x_13 --> x_3, x_14 --> x_1, x_14 --> x_4, x_15 --> x_1, x_15 --> x_13, x_2 --> x_11, x_2 --> x_4, x_2 --> x_8, x_3 --> x_15, x_6 --> x_11, x_6 --> x_15, x_7 --> x_8, x_8 --> x_3

```

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
