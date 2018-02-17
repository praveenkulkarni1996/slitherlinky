# slitherlinky
A solver for Slitherlink (also called Loop-the-Loop) that uses SAT.


## About the game
Slitherlink, also called Loop the Loop in India, (and a plethora of other names
all over the world) is a logic puzzle. You can read more about it on
[Wikipedia]. Because it appears in the most popular English newspaper in India,
it is quite popular amongst Indians. 

Slitherlink is played on a rectangular lattice of dots. Some of the squares
formed by the dots have numbers inside them. The objective is to connect
horizontally and vertically adjacent dots so that the lines form a simple loop
with no loose ends. In addition, the number inside a square represents how many
of its four sides are segments in the loop.

*Slitherlinky* is a solver for slitherlink puzzles. Slitherlinky reduces a
puzzle to a SAT problem, which is solved by a SAT solver. 

## SAT queries

There are three constraints in Slitherlink that need to be expressed to the SAT
solver. The choice of boolean variables is also decided accordingly. 

* **Cell Imposed Constraints:** This is the obvious one. Every cell with a
  number inside should have equivalent number of edges. 

* **Loop Constraints:** Every corner should be part of either 0 or 2 edges. This
  is sufficient to ensure that edges form a loop.

* **Single Loop Constraints:** The above two conditions do not restrict multiple
  loops from being formed. For that, we would require a predicate variable for
  connected relation which is a transitive closure of the adjacency relation for
  edges.

There are two kinds of variables that are needed to express this problem. 

* **Edge Variables:** Every possible edge is represented by a boolean. If the
  variable is true in a satisfiable solution, then there is an edge in that
  position. *Notation: e(i) represents the edge i*.

* **Connected Variables:** There are E * E such variables, where E is the number
  of edges. *Notation c(i, j) represents that e(i) and e(j) are connected*.
  These variables are required to express the Single Loop Constraints described
  above.

  If e(i) and e(j) correspond to adjacent edges, then e(i) AND e(j) <=> c(i, j).
  If they are not adjacent, then we need to express this recursively as follows. 
  e(i) AND e(j) AND ((e(k1) AND c(k1, j) OR (e(k2) AND c(k2, j) ..) <=> c(i, j).

## Getting Started

### Prerequisites

Slitherlink is written in [Python3]. It also requires a SAT solver. 

### Installing

### Todo
Finish the README.  Add the code.

[Wikipedia]: https://en.wikipedia.org/wiki/Slitherlink
[Python3]: https://www.python.org/downloads/
