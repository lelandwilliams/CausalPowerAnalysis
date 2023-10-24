# CausalPowerAnalysis
code to perform causal power analysis from teh Kummerfeld, Williams, and Ma paper.
We created a set of generating causal graphs, and used them to generate statisticly normal data,
then tested the pc algorithm to determine the success rates in finding correct links in the correct direction.

We also assigned a random seed to each generating graph, so that each run with a given graph would use the same data.

## Basic Usage
In a simpler use case, you can test the strength of one run on a given generator graph by typing

python discover.py nodes r graphnum graph seed index

where nodes is the number of nodes in the data strength
r is the effect size between nodes
graphnum is an identifier for the number of the graph
graph is a string of the form "a --> b, b --> c " giving the names of the nodes and the causal direction between them.
seed is a random seed
index is the directory number.

## Explanation
We found that creating the graphs that satisfy our conditions (no incoming variance > 0.9) could be time consuming,
so we created the graphs first. We also specified a random seed used in generating the fake data from the graph.
